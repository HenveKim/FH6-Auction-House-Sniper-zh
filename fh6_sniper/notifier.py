"""Purchase CSV logging and sound/toast notifications."""
from __future__ import annotations
import csv
import datetime as dt
from pathlib import Path


def log_purchase(log_path, outcome: str, loop_seconds: float,
                 total: int) -> None:
    """Append one row to the purchase CSV. Writes a header if new."""
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(
                ["timestamp", "outcome", "loop_seconds", "total_bought"])
        writer.writerow([
            dt.datetime.now().isoformat(timespec="seconds"),
            outcome, f"{loop_seconds:.1f}", total,
        ])


def notify_success(car_count: int, sound: bool, toast: bool) -> None:
    """成功买断后播放提示音并显示 Windows 通知。"""
    if sound:
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass
    if toast:
        try:
            from win11toast import toast as show_toast
            show_toast("FH6 蹲守系统",
                       f"已买到车辆（本次运行共 {car_count} 辆）")
        except Exception:
            pass
