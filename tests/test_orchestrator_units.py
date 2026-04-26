"""Orchestrator pure-unit tests — no asyncio, no real devices, no API."""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from doppelvoice.config import AppConfig, Credentials
from doppelvoice.engine.doubao import TranslationEvent
from doppelvoice.pipeline.orchestrator import (
    Orchestrator,
    _FatalRemote,
    _TRANSIENT_CODES,
    _drain_queue,
)


@pytest.fixture
def cfg():
    return AppConfig(credentials=Credentials(app_key="k", access_key="s"))


@pytest.fixture
def orch(cfg):
    # Orchestrator.__init__ calls cfg.snapshot() — no I/O
    return Orchestrator(cfg)


# ── _drain_queue ──────────────────────────────────────────────────────────────

def test_drain_queue_empty_returns_zero():
    q: asyncio.Queue = asyncio.Queue()
    assert _drain_queue(q) == 0


def test_drain_queue_returns_count_and_empties():
    q: asyncio.Queue = asyncio.Queue()
    for i in range(5):
        q.put_nowait(b"x")
    n = _drain_queue(q)
    assert n == 5
    assert q.empty()


# ── _handle_error ─────────────────────────────────────────────────────────────

def test_handle_error_transient_raises_runtime(orch):
    for code in (11301, 11303, 21300):
        ev = TranslationEvent(kind="error", status_code=code, message="retry")
        with pytest.raises(RuntimeError, match="remote transient"):
            orch._handle_error(ev)


def test_handle_error_fatal_raises_fatal_remote(orch):
    ev = TranslationEvent(kind="error", status_code=11500, message="bad auth")
    with pytest.raises(_FatalRemote) as exc_info:
        orch._handle_error(ev)
    assert exc_info.value.code == 11500


def test_handle_error_unknown_code_is_fatal(orch):
    """A code not in _TRANSIENT_CODES must raise _FatalRemote."""
    code = 99999
    assert code not in _TRANSIENT_CODES
    ev = TranslationEvent(kind="error", status_code=code, message="nope")
    with pytest.raises(_FatalRemote):
        orch._handle_error(ev)


# ── _handle_subtitle ─────────────────────────────────────────────────────────

def test_handle_subtitle_empty_text_no_emit(orch):
    bus = MagicMock()
    orch.event_bus = bus
    ev = TranslationEvent(kind="target_text", text="   ")
    orch._handle_subtitle(ev)
    bus.emit.assert_not_called()


def test_handle_subtitle_target_text_emits(orch):
    bus = MagicMock()
    orch.event_bus = bus
    ev = TranslationEvent(kind="target_text", text="hello")
    orch._handle_subtitle(ev)
    bus.emit.assert_called_once_with(ev)


# ── _handle_audio (event_bus path) ───────────────────────────────────────────

def test_handle_audio_emits_to_bus(orch):
    bus = MagicMock()
    orch.event_bus = bus

    from doppelvoice.pipeline.orchestrator import _ReceiverContext
    ctx = _ReceiverContext(decoder=None, playback_sr=48000, dump_root=None)
    playback = MagicMock()

    ev = TranslationEvent(kind="audio", audio=b"\x00\x01")
    orch._handle_audio(ev, ctx, playback)

    bus.emit.assert_called_once_with(ev)
    playback.push_pcm.assert_called_once_with(b"\x00\x01")


# ── _FatalRemote ──────────────────────────────────────────────────────────────

def test_fatal_remote_str_contains_code_and_msg():
    exc = _FatalRemote(11500, "auth error")
    assert "11500" in str(exc)
    assert "auth error" in str(exc)


def test_fatal_remote_none_values():
    exc = _FatalRemote(None, None)
    assert exc.code is None
    assert exc.message is None
