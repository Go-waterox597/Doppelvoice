"""GUI 入口：qasync 把 asyncio 跑在 Qt 主循环上。

启动流程：
1. 加载配置（密钥缺失也不抛异常，进 GUI 后引导填写）
2. 应用深色主题
3. 创建主窗口
4. 检测 .env 是否有密钥，无则弹设置对话框
"""
from __future__ import annotations

import asyncio
import sys

import qasync
from loguru import logger
from PySide6.QtWidgets import QApplication

from doppelvoice.config import AppConfig, Credentials
from doppelvoice.gui.env_io import has_credentials, read_env
from doppelvoice.gui.i18n import i18n
from doppelvoice.gui.main_window import MainWindow
from doppelvoice.gui.settings_dialog import SettingsDialog
from doppelvoice.gui.theme import stylesheet
from doppelvoice.utils.log import setup_logging


def _load_or_dummy_config() -> AppConfig:
    """优先从 .env 加载；密钥缺失时返回占位 cfg，让用户在 GUI 里填。"""
    try:
        return AppConfig.load()
    except RuntimeError:
        env = read_env()
        cred = Credentials(
            app_key=env.get("DOUBAO_APP_KEY", ""),
            access_key=env.get("DOUBAO_ACCESS_KEY", ""),
            resource_id=env.get("DOUBAO_RESOURCE_ID", "volc.service_type.10053"),
        )
        return AppConfig(credentials=cred)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Doppelvoice")

    cfg = _load_or_dummy_config()
    setup_logging(cfg.log_dir, cfg.log_level)
    logger.info("GUI starting (lang={})", i18n.lang)

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    theme = "dark"
    app.setStyleSheet(stylesheet(theme))

    win = MainWindow(cfg, i18n, theme=theme)
    win.show()

    # 启动预检：VB-Audio Virtual Cable 没装则弹"下载"对话框
    from doppelvoice.audio import devices as audio_devices
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import QMessageBox
    if audio_devices.find_device("CABLE Input", need_output=True) is None:
        box = QMessageBox(win)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(i18n.t("dialog.error.cable_missing.title"))
        box.setText(i18n.t("dialog.error.cable_missing.body"))
        download_btn = box.addButton(
            i18n.t("dialog.error.cable_missing.download"),
            QMessageBox.ButtonRole.AcceptRole,
        )
        box.addButton(QMessageBox.StandardButton.Close)
        box.exec()
        if box.clickedButton() is download_btn:
            QDesktopServices.openUrl(QUrl("https://vb-audio.com/Cable/"))

    if not has_credentials():
        logger.info("no credentials, opening settings dialog")
        dlg = SettingsDialog(cfg, i18n, win)
        dlg.exec()

    with loop:
        return loop.run_forever() or 0


if __name__ == "__main__":
    sys.exit(main())
