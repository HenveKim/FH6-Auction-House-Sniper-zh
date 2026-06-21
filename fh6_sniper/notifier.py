"""Purchase CSV logging and sound/toast notifications."""
from __future__ import annotations
import csv
import datetime as dt
from pathlib import Path


def purchase_timestamp() -> dt.datetime:
    """Return the local timestamp used for purchase records and notifications."""
    return dt.datetime.now().replace(microsecond=0)


def format_purchase_time(purchased_at: dt.datetime) -> str:
    return purchased_at.strftime("%Y-%m-%d %H:%M:%S")


def log_purchase(log_path, outcome: str, loop_seconds: float,
                 total: int, purchased_at: dt.datetime | None = None) -> None:
    """Append one row to the purchase CSV. Writes a header if new."""
    purchased_at = purchased_at or purchase_timestamp()
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(
                ["timestamp", "outcome", "loop_seconds", "total_bought"])
        writer.writerow([
            purchased_at.isoformat(timespec="seconds"),
            outcome, f"{loop_seconds:.1f}", total,
        ])


def notify_success(car_count: int, sound: bool, toast: bool,
                   purchased_at: dt.datetime | None = None) -> None:
    """成功买断后播放提示音并显示 Windows 通知。"""
    purchased_at = purchased_at or purchase_timestamp()
    if sound:
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass
    if toast:
        try:
            from win11toast import toast as show_toast
            show_toast(
                "FH6 蹲守系统",
                f"成功买到第 {car_count} 辆车\n"
                f"时间：{format_purchase_time(purchased_at)}")
        except Exception:
            pass
