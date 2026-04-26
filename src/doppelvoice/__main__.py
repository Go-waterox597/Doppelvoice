"""python -m doppelvoice 入口。

Bundle 模式（PyInstaller 打包后双击 Doppelvoice.exe 启动）：
若用户没有显式传任何参数，默认进 GUI；CLI 子命令仍可通过
`Doppelvoice.exe --check` 等方式触发。开发模式 `python -m doppelvoice`
行为不变（默认走 CLI）。

最后一道闸：用 sys.excepthook + try/except 包住 main()，把任何未捕获
异常先写到 %APPDATA%\\Doppelvoice\\logs\\crash.log，再用最低限的 Qt
弹窗（如果可用）告诉用户。绝不让用户看到 PyInstaller 默认的
"Unhandled exception in script"，因为那个对话框啥定位信息都没有，
还会让人以为是 .exe 损坏。
"""
import sys
import traceback
from pathlib import Path

from doppelvoice.cli import main


def _crash_log_path() -> Path:
    """与 config._resolve_project_root 保持同源 —— frozen 模式写 APPDATA。"""
    if getattr(sys, "frozen", False):
        if sys.platform == "win32":
            import os
            base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData/Roaming")))
        elif sys.platform == "darwin":
            base = Path.home() / "Library/Application Support"
        else:
            import os
            base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
        return base / "Doppelvoice" / "logs" / "crash.log"
    return Path(__file__).resolve().parents[2] / "logs" / "crash.log"


def _last_resort_handle(exc_type, exc_value, exc_tb) -> None:
    """所有未捕获异常的兜底：写 crash.log + 弹 Qt 错误框（能弹则弹）。"""
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    # 1) 写 crash.log（永远尝试，即使 logger 还没装好）
    try:
        path = _crash_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            import datetime
            f.write(f"\n=== {datetime.datetime.now().isoformat()} ===\n")
            f.write(tb_text)
    except Exception:
        pass  # 写不成就算了，不能因为日志不能写再崩一次
    # 2) 尝试弹 Qt 框（PySide6 已在 venv 里，但启动前/后都可能挂）
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "Doppelvoice — Unexpected error",
            f"Doppelvoice crashed and will exit.\n\n"
            f"A full traceback has been written to:\n{_crash_log_path()}\n\n"
            f"Top of trace:\n{tb_text[-1500:]}",
        )
    except Exception:
        pass
    # 3) 仍然走默认 hook（如果 stderr 不是 None 会打 traceback；否则吞掉但 crash.log 已落盘）
    if sys.stderr is not None:
        sys.__excepthook__(exc_type, exc_value, exc_tb)


if __name__ == "__main__":
    sys.excepthook = _last_resort_handle

    # Windows 控制台默认 GBK，Python 3.7+ 下 stdout/stderr 默认走 UTF-8 编码会导致
    # 中文错误消息显示为 mojibake。强制 reconfigure 到 utf-8 让用户看清错误。
    # 注意：PyInstaller windowed bundle (onefile + console=False) 下 stdio 是 None。
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            if stream is None:
                continue
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError):
                pass
    if getattr(sys, "frozen", False) and len(sys.argv) == 1:
        sys.argv.append("--gui")
    sys.exit(main())
