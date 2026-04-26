"""Qt 信号总线：pipeline 事件 → GUI。"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from doppelvoice.engine.doubao import TranslationEvent


class GuiEventBus(QObject):
    # (text, is_definite)
    source_text = Signal(str, bool)
    target_text = Signal(str, bool)
    # audio bytes length
    audio_received = Signal(int)
    # status: "idle" | "connecting" | "running" | "error" | "stopped"
    status = Signal(str, str)  # status_key, human message
    # arbitrary error
    error = Signal(str)

    # NOTE: 该总线必须在 GUI 主线程构造（main_window.__init__ 里 ✓）。
    # qasync 把 asyncio loop 跑在 Qt 主线程，emit 都是 Direct Connection；
    # 若未来 orchestrator 移到独立线程，emit 自动走 Queued Connection 仍安全。

    def emit_event(self, ev: TranslationEvent) -> None:
        """Orchestrator 调用：把 TranslationEvent 分发到对应 signal。"""
        if ev.kind == "source_text" and ev.text:
            self.source_text.emit(ev.text, ev.is_definite)
        elif ev.kind == "target_text" and ev.text:
            self.target_text.emit(ev.text, ev.is_definite)
        elif ev.kind == "audio" and ev.audio:
            self.audio_received.emit(len(ev.audio))
        elif ev.kind == "error":
            self.error.emit(f"code={ev.status_code} msg={ev.message}")

    # 兼容 EventBus Protocol
    def emit(self, ev: TranslationEvent) -> None:
        self.emit_event(ev)
