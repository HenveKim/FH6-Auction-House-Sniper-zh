"""Entry point: wires config, templates, sniper, overlay, and hotkeys."""
from __future__ import annotations
import json
import logging
import os
import sys
import threading
from dataclasses import asdict
from pathlib import Path


def _app_dir_for_self_test() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _resource_dir_for_self_test() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def _run_self_test() -> int:
    """Validate a source or frozen build without starting the GUI."""
    import importlib
    import traceback

    app_dir = _app_dir_for_self_test()
    resource_dir = _resource_dir_for_self_test()
    log_dir = app_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "self-test.log"
    lines = ["FH6 Sniper self-test"]
    ok = True

    def write_log():
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    write_log()

    def check(name, fn):
        nonlocal ok
        lines.append(f"RUN {name}")
        write_log()
        try:
            detail = fn()
            lines.append(f"OK {name}: {detail or ''}".rstrip())
        except Exception as exc:
            ok = False
            lines.append(f"FAIL {name}: {exc}")
            lines.append(traceback.format_exc().rstrip())
        write_log()

    for module in (
            "cv2", "numpy", "mss", "bettercam", "pynput", "win32gui",
            "win32api", "windows_capture"):
        check(f"import {module}", lambda m=module: importlib.import_module(m))

    def _tk_check():
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.update_idletasks()
        root.destroy()
        return f"Tk {tk.TkVersion}"

    check("tkinter", _tk_check)

    def _templates_check():
        from fh6_sniper import vision
        en_templates = vision.load_templates(resource_dir / "templates")
        zh_templates = vision.load_templates(resource_dir / "templates_zh-CN")
        return f"en-US={len(en_templates)} zh-CN={len(zh_templates)}"

    check("templates", _templates_check)

    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if ok else 1


def _self_test_requested() -> bool:
    if "--self-test" in sys.argv:
        return True
    if os.environ.get("FH6_SNIPER_SELF_TEST") == "1":
        return True
    if getattr(sys, "frozen", False):
        candidates = {Path(sys.executable).parent}
        bundle_dir = getattr(sys, "_MEIPASS", None)
        if bundle_dir:
            candidates.add(Path(bundle_dir).parent)
        return any((path / "self-test.request").exists()
                   for path in candidates)
    return False


if _self_test_requested():
    raise SystemExit(_run_self_test())

from pynput import keyboard

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from fh6_sniper import capture, events, notifier, paths, vision
    from fh6_sniper.config import load_config, save_config
    from fh6_sniper.overlay import Overlay
    from fh6_sniper.sniper import GameIO, Sniper
else:
    from . import capture, events, notifier, paths, vision
    from .config import load_config, save_config
    from .overlay import Overlay
    from .sniper import GameIO, Sniper


def _prefer_utf8_console() -> None:
    """Keep IDE runner output readable when it expects UTF-8 on Windows."""
    for stream in (sys.stdout, sys.stderr):
        if stream is None or not hasattr(stream, "reconfigure"):
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _log_config(cfg) -> None:
    """Dump the loaded config to the log as a single JSON line.
    Helps when triaging user-submitted logs - we can see what the bot
    was configured with at session start."""
    body = asdict(cfg)
    declared = set(cfg.__dataclass_fields__)
    for key, value in cfg.__dict__.items():           # include extras
        if key not in declared:
            body[key] = value
    body = {k: list(v) if isinstance(v, tuple) else v for k, v in body.items()}
    logging.getLogger("fh6").info("config snapshot: %s",
                                   json.dumps(body, sort_keys=True))


class OverlayEventHandler(logging.Handler):
    """Send user-facing event records to the Tk overlay safely."""

    def __init__(self, overlay):
        super().__init__(level=logging.INFO)
        self.overlay = overlay

    def emit(self, record):
        try:
            self.overlay.add_log_record(record)
        except Exception:
            pass


def _setup_logging():
    _prefer_utf8_console()
    log_path = paths.app_dir() / "logs" / "sniper.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)s %(message)s", "%H:%M:%S")
    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setFormatter(fmt)
    root = logging.getLogger("fh6")
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(file_handler)
    if sys.stderr is not None:          # no console under --windowed exe
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        root.addHandler(console)
    return log_path


def main() -> None:
    log_path = _setup_logging()
    logging.getLogger("fh6").info("FH6 Sniper starting (log: %s)", log_path)
    cfg = load_config(paths.app_dir() / "config.json")
    _log_config(cfg)
    templates = vision.load_templates(
        paths.resource_dir() / cfg.effective_template_dir(),
        moving_background=cfg.moving_background)
    io = GameIO(cfg, templates)
    overlay = Overlay(
        hide_from_capture=not getattr(cfg, "overlay_capturable", False))
    event_logger = logging.getLogger(events.LOGGER_NAME)
    event_handler = OverlayEventHandler(overlay)
    event_logger.addHandler(event_handler)
    events.info("程序启动")

    state = {
        "sniper": None,
        "thread": None,
        # display-side running totals - accumulate across stop/start cycles
        # so the overlay's BOUGHT / SEARCHES / FAILS don't reset every run.
        "display": {"searches": 0, "bought": 0, "fails": 0},
        # last raw values seen from the current Sniper - used to compute
        # deltas (new Sniper instances start their internal counters at 0).
        "last_bot_stats": (0, 0, 0),
    }
    purchase_log = paths.app_dir() / cfg.log_path

    def on_purchase(loop_seconds, total):
        purchased_at = notifier.purchase_timestamp()
        notifier.log_purchase(
            purchase_log, "bought", loop_seconds, total, purchased_at)
        notifier.notify_success(
            total, cfg.notify_sound, cfg.notify_toast, purchased_at)
        events.success(
            "购车成功：第 %d 辆，时间 %s",
            total, notifier.format_purchase_time(purchased_at))

    def on_stats(searches, bought, fails):
        last_s, last_b, last_f = state["last_bot_stats"]
        d = state["display"]
        d["searches"] += max(0, searches - last_s)
        d["bought"]   += max(0, bought   - last_b)
        d["fails"]    += max(0, fails    - last_f)
        state["last_bot_stats"] = (searches, bought, fails)
        overlay.set_stats(d["searches"], d["bought"], d["fails"])

    def start():
        if state["thread"] and state["thread"].is_alive():
            return
        events.info("开始蹲守")
        if cfg.win32_api_input:
            logging.getLogger("fh6.main").info(
                "background input enabled; leaving FH6 focus unchanged")
        else:
            capture.focus_window(cfg.window_title)
        capture.reset_normalize_plan()             # detect crop afresh each run
        state["last_bot_stats"] = (0, 0, 0)        # new Sniper, fresh deltas
        sniper = Sniper(io, cfg, on_purchase=on_purchase,
                        on_status=overlay.set_status,
                        on_stats=on_stats)

        def _run_safe():
            try:
                sniper.run()
            except Exception:
                logging.getLogger("fh6.main").exception(
                    "sniper thread crashed")
                events.error("线程崩溃，请查看 sniper.log")
                try:
                    overlay.set_status("崩溃：请查看 sniper.log")
                except Exception:
                    pass

        thread = threading.Thread(target=_run_safe, daemon=True)
        state["sniper"], state["thread"] = sniper, thread
        thread.start()

    def stop():
        if state["sniper"]:
            events.info("请求停止")
            state["sniper"].request_stop()

    def toggle():
        if state["thread"] and state["thread"].is_alive():
            stop()
        else:
            start()

    hotkeys_ref = {"listener": None}

    def _bind_hotkeys(start_stop, panic):
        listener = keyboard.GlobalHotKeys({start_stop: toggle, panic: stop})
        listener.start()
        hotkeys_ref["listener"] = listener

    _bind_hotkeys(cfg.hotkey_start_stop, cfg.hotkey_panic)

    def apply_settings(values):
        """Apply settings dict to cfg in-place; persist; reload as needed."""
        log = logging.getLogger("fh6.settings")
        prev_bg = cfg.moving_background
        prev_template_dir = cfg.effective_template_dir()
        prev_start = cfg.hotkey_start_stop
        prev_panic = cfg.hotkey_panic
        prev_capturable = getattr(cfg, "overlay_capturable", False)
        prev_window_capture = getattr(cfg, "window_content_capture", False)
        diffs = []
        for key, value in values.items():
            if key == "game_language" and value not in ("en-US", "zh-CN"):
                value = "en-US"
            old = getattr(cfg, key, None)
            if old != value:
                diffs.append(f"{key} {old!r} -> {value!r}")
            setattr(cfg, key, value)
        if diffs:
            log.info("settings changed: %s", ", ".join(diffs))
        if cfg.overlay_capturable != prev_capturable:
            overlay.set_capturable(cfg.overlay_capturable)
            log.info("overlay capturable -> %s", cfg.overlay_capturable)
        if cfg.window_content_capture != prev_window_capture:
            capture.reset_normalize_plan()
            log.info("background window capture -> %s",
                     cfg.window_content_capture)
        next_template_dir = cfg.effective_template_dir()
        if (cfg.moving_background != prev_bg
                or next_template_dir != prev_template_dir):
            try:
                new_templates = vision.load_templates(
                    paths.resource_dir() / next_template_dir,
                    moving_background=cfg.moving_background)
            except Exception as exc:
                log.exception("template reload failed")
                events.error("模板重新加载失败：%s", exc)
                return f"设置未保存：模板重新加载失败：{exc}"
            io.templates = new_templates
            log.info("templates reloaded (dir=%s, moving_background=%s)",
                     next_template_dir, cfg.moving_background)
        try:
            save_config(cfg, paths.app_dir() / "config.json")
        except Exception as exc:
            log.exception("save_config failed")
            events.error("配置保存失败：%s", exc)
            return f"无法保存配置：{exc}"
        events.info("设置已保存：%d 项变更", len(diffs))
        if (cfg.hotkey_start_stop != prev_start
                or cfg.hotkey_panic != prev_panic):
            try:
                if hotkeys_ref["listener"] is not None:
                    hotkeys_ref["listener"].stop()
                _bind_hotkeys(cfg.hotkey_start_stop, cfg.hotkey_panic)
                log.info("hotkeys rebound (%s / %s)",
                         cfg.hotkey_start_stop, cfg.hotkey_panic)
            except Exception as exc:
                log.exception("hotkey rebind failed")
                return f"已保存，但热键重新绑定失败：{exc}"
        return None

    overlay.bind_settings(cfg)
    overlay.on_save(apply_settings)
    overlay.on_toggle(toggle)
    overlay.set_status("空闲")
    try:
        overlay.run()
    finally:
        events.info("程序退出")
        stop()
        listener = hotkeys_ref["listener"]
        if listener is not None:
            listener.stop()
        event_logger.removeHandler(event_handler)


if __name__ == "__main__":
    main()
