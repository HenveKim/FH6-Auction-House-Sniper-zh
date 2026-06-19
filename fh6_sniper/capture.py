"""Screen capture and window-focus helpers."""
from __future__ import annotations
import logging
import threading
import time
import numpy as np
import cv2
import win32con
import win32gui

_log = logging.getLogger("fh6.capture")

CANON = (1920, 1080)

_camera = None
_camera_unavailable = False
_hwnd_cache: dict = {}
_window_capture_sessions: dict[int, "_WindowCaptureSession"] = {}
_window_capture_lock = threading.Lock()
_window_capture_unavailable = False
_window_capture_logged: set[str] = set()


def find_window(title: str) -> int:
    """Return the hwnd of a visible window with this title, or 0."""
    cached = _hwnd_cache.get(title)
    if cached and win32gui.IsWindow(cached):
        return cached
    matches = []

    def _collect(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            if win32gui.GetWindowText(hwnd).strip() == title:
                matches.append(hwnd)

    win32gui.EnumWindows(_collect, None)
    hwnd = matches[0] if matches else 0
    if hwnd:
        _hwnd_cache[title] = hwnd
    return hwnd


def client_rect(hwnd: int):
    """Return (left, top, width, height) of a window's client area."""
    cl, ct, cr, cb = win32gui.GetClientRect(hwnd)
    width, height = cr - cl, cb - ct
    sx, sy = win32gui.ClientToScreen(hwnd, (cl, ct))
    return sx, sy, width, height


def using_dxgi() -> bool:
    return _camera is not None and not _camera_unavailable


def _grab_dxgi(region):
    global _camera, _camera_unavailable
    if _camera_unavailable:
        return None
    try:
        import bettercam
        if _camera is None:
            _camera = bettercam.create(output_idx=0, output_color="BGR")
        for _ in range(5):
            frame = _camera.grab(region=region) if region else _camera.grab()
            if frame is not None:
                return np.ascontiguousarray(frame)
            time.sleep(0.008)
        return None
    except Exception:
        _camera_unavailable = True
        return None


def _grab_mss(region):
    import mss
    with mss.MSS() as sct:
        if region:
            area = {"left": region[0], "top": region[1],
                    "width": region[2] - region[0],
                    "height": region[3] - region[1]}
        else:
            area = sct.monitors[1]
        shot = sct.grab(area)
        return np.ascontiguousarray(np.array(shot)[:, :, :3])


def _log_window_capture_once(key: str, level: int, msg: str, *args) -> None:
    if key in _window_capture_logged:
        return
    _window_capture_logged.add(key)
    _log.log(level, msg, *args)


class _WindowCaptureSession:
    """Small wrapper around windows-capture's callback-style API."""

    def __init__(self, hwnd: int):
        self.hwnd = hwnd
        self.latest: np.ndarray | None = None
        self.closed = False
        self.control = None
        self._lock = threading.Lock()
        self._start()

    def _start(self) -> None:
        from windows_capture import WindowsCapture

        cap = WindowsCapture(
            window_hwnd=self.hwnd,
            cursor_capture=False,
            draw_border=False,
            minimum_update_interval=16)

        @cap.event
        def on_frame_arrived(frame, _control):
            try:
                bgr = frame.convert_to_bgr().frame_buffer
                bgr = np.ascontiguousarray(bgr)
                with self._lock:
                    self.latest = bgr
            except Exception as exc:
                _log_window_capture_once(
                    f"frame-{self.hwnd}", logging.DEBUG,
                    "background window frame conversion failed: %s", exc)

        @cap.event
        def on_closed():
            self.closed = True

        self.control = cap.start_free_threaded()

    def get_frame(self, wait_s: float = 0.18) -> np.ndarray | None:
        deadline = time.monotonic() + wait_s
        while time.monotonic() <= deadline:
            if self.closed:
                return None
            try:
                if self.control is not None and self.control.is_finished():
                    self.closed = True
                    return None
            except Exception:
                self.closed = True
                return None
            with self._lock:
                frame = self.latest
            if frame is not None:
                return frame
            time.sleep(0.01)
        return None

    def stop(self) -> None:
        try:
            if self.control is not None:
                self.control.stop()
        except Exception:
            pass
        self.closed = True


def _grab_window_content(hwnd: int) -> np.ndarray | None:
    """Try Windows Graphics Capture for an hwnd. Returns raw BGR or None."""
    global _window_capture_unavailable
    if _window_capture_unavailable:
        return None
    if not hwnd or not win32gui.IsWindow(hwnd):
        return None
    if win32gui.IsIconic(hwnd):
        _log_window_capture_once(
            f"minimized-{hwnd}", logging.INFO,
            "background window capture skipped: FH6 is minimized")
        return None

    try:
        with _window_capture_lock:
            session = _window_capture_sessions.get(hwnd)
            if session is None or session.closed:
                session = _WindowCaptureSession(hwnd)
                _window_capture_sessions[hwnd] = session
                _log.info("background window capture started (hwnd=%s)", hwnd)
        frame = session.get_frame()
    except ImportError as exc:
        _window_capture_unavailable = True
        _log_window_capture_once(
            "import", logging.WARNING,
            "background window capture unavailable: %s", exc)
        return None
    except Exception as exc:
        _log_window_capture_once(
            f"start-{hwnd}", logging.WARNING,
            "background window capture failed; falling back to screen region: %s",
            exc)
        return None

    if frame is None or frame.size == 0:
        _log_window_capture_once(
            f"empty-{hwnd}", logging.INFO,
            "background window capture has no frame yet; using screen region")
        return None
    if frame.max() < _BLACK_THRESHOLD:
        _log_window_capture_once(
            f"blank-{hwnd}", logging.INFO,
            "background window capture returned a blank frame; using screen region")
        return None
    return frame


_capture_failing = False

# Treat any pixel below this 0-255 grayscale value as solid-black background.
_BLACK_THRESHOLD = 6
# Refuse to strip bars if doing so removes more than this fraction of either
# axis. Guards against dark scenes / load screens that look like a black bar.
_MAX_STRIP_FRACTION = 0.5
# Aspect-ratio tolerance: within this fraction of 16:9 counts as 16:9.
_ASPECT_EPS = 0.01


def _symmetric_strip(near: int, far: int) -> int:
    """Return the per-side strip if `near` and `far` look like matching bars,
    else 0. Natural interior dark is asymmetric; real letterbox / pillarbox
    is centered, so the two edges should agree within tolerance."""
    if near == 0 and far == 0:
        return 0
    tol = max(5, int(max(near, far) * 0.10))
    if abs(near - far) > tol:
        return 0
    return min(near, far)


def _detect_strip_box(frame: np.ndarray):
    """Return (top, bottom, left, right) inner-rect coords for a symmetric
    black-bar strip, or None if no reliable bar is present."""
    if frame.size == 0:
        return None
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    row_lit = gray.max(axis=1) >= _BLACK_THRESHOLD
    col_lit = gray.max(axis=0) >= _BLACK_THRESHOLD
    if not row_lit.any() or not col_lit.any():
        return None
    top_dark = int(np.argmax(row_lit))
    bottom_dark = int(np.argmax(row_lit[::-1]))
    left_dark = int(np.argmax(col_lit))
    right_dark = int(np.argmax(col_lit[::-1]))
    vert = _symmetric_strip(top_dark, bottom_dark)
    horiz = _symmetric_strip(left_dark, right_dark)
    if vert == 0 and horiz == 0:
        return None
    new_h = h - 2 * vert
    new_w = w - 2 * horiz
    if new_h < h * _MAX_STRIP_FRACTION or new_w < w * _MAX_STRIP_FRACTION:
        return None
    return (vert, h - vert, horiz, w - horiz)


def _strip_black_bars(frame: np.ndarray) -> np.ndarray:
    """Apply the symmetric-bar strip directly. Thin wrapper around
    `_detect_strip_box` for tests + ad-hoc one-off use."""
    box = _detect_strip_box(frame)
    if box is None:
        return frame
    t, b, l, r = box
    return frame[t:b, l:r]


def _detect_aspect_box(h: int, w: int):
    """Return (top, bottom, left, right) for the largest centered 16:9
    sub-rect, or None if `(h, w)` already match 16:9 within tolerance."""
    if h == 0 or w == 0:
        return None
    target = CANON[0] / CANON[1]                     # 16/9
    current = w / h
    if abs(current - target) <= _ASPECT_EPS:
        return None
    if current > target:                             # frame is too wide
        crop_w = int(round(h * target))
        x = (w - crop_w) // 2
        return (0, h, x, x + crop_w)
    crop_h = int(round(w / target))                  # frame is too tall
    y = (h - crop_h) // 2
    return (y, y + crop_h, 0, w)


# Plan: cached crop boxes + resize flag, keyed on the input frame shape.
# Computed once from a real game frame, then reused on every poll - turns
# normalisation into a pair of array slices plus an optional resize.
_plan: dict | None = None


def _build_plan(frame: np.ndarray) -> dict:
    strip = _detect_strip_box(frame)
    if strip:
        t, b, l, r = strip
        h, w = b - t, r - l
    else:
        h, w = frame.shape[:2]
    aspect = _detect_aspect_box(h, w)
    if aspect:
        t2, b2, l2, r2 = aspect
        h, w = b2 - t2, r2 - l2
    return {
        "input_shape": frame.shape,
        "strip": strip,
        "aspect": aspect,
        "needs_resize": (w, h) != CANON,
    }


def reset_normalize_plan() -> None:
    """Drop the cached plan so the next normalize_frame call re-detects.
    Call this whenever the capture region or game settings change (e.g.
    when the user hits Start)."""
    global _plan
    _plan = None


def normalize_frame(frame: np.ndarray) -> np.ndarray:
    """Apply the cached strip / 16:9 crop / 1080p resize plan; build the
    plan from this frame if none is cached yet or the input shape changed."""
    global _plan
    if frame is None or frame.size == 0:
        return np.zeros((CANON[1], CANON[0], 3), dtype=np.uint8)
    if _plan is None or _plan["input_shape"] != frame.shape:
        # Skip caching a plan derived from a totally blank frame (capture
        # failure fallback). Without this, a transient blank stays cached.
        if frame.max() < _BLACK_THRESHOLD:
            return cv2.resize(frame, CANON, interpolation=cv2.INTER_AREA) \
                if (frame.shape[1], frame.shape[0]) != CANON else frame
        _plan = _build_plan(frame)
        _log.info("normalize plan: input=%s strip=%s aspect=%s resize=%s",
                  frame.shape, _plan["strip"], _plan["aspect"],
                  _plan["needs_resize"])
    plan = _plan
    if plan["strip"]:
        t, b, l, r = plan["strip"]
        frame = frame[t:b, l:r]
    if plan["aspect"]:
        t, b, l, r = plan["aspect"]
        frame = frame[t:b, l:r]
    if plan["needs_resize"]:
        frame = cv2.resize(frame, CANON, interpolation=cv2.INTER_AREA)
    return frame


def grab_screen(window_title: str | None = None,
                use_window_capture: bool = False) -> np.ndarray:
    """Capture a BGR 1920x1080 frame. Falls back to mss on DXGI failure;
    returns a blank frame if both backends fail."""
    global _capture_failing
    region = None
    hwnd = 0
    if window_title:
        hwnd = find_window(window_title)
        if hwnd:
            if use_window_capture:
                frame = _grab_window_content(hwnd)
                if frame is not None:
                    if _capture_failing:
                        _log.info("capture recovered")
                        _capture_failing = False
                    return normalize_frame(frame)
            x, y, w, h = client_rect(hwnd)
            if w > 0 and h > 0:
                region = (x, y, x + w, y + h)
    frame = _grab_dxgi(region)
    if frame is None:
        try:
            frame = _grab_mss(region)
        except Exception as e:
            if not _capture_failing:
                _log.warning("capture failed: %s", e)
                _capture_failing = True
            frame = None
    if frame is None:
        return np.zeros((CANON[1], CANON[0], 3), dtype=np.uint8)
    if _capture_failing:
        _log.info("capture recovered")
        _capture_failing = False
    return normalize_frame(frame)


def foreground_title() -> str:
    return win32gui.GetWindowText(win32gui.GetForegroundWindow())


def is_game_focused(expected_title: str, title_getter=foreground_title) -> bool:
    return title_getter().strip() == expected_title


def focus_window(title: str) -> bool:
    """Bring the named window to the foreground. Returns True on success."""
    hwnd = find_window(title)
    if not hwnd:
        return False
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False
