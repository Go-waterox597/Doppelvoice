"""OggOpusDecoder unit tests — no real audio, no external API."""
from __future__ import annotations

import pytest

from doppelvoice.audio.opus_decoder import OggOpusDecoder


def test_initial_state_empty():
    d = OggOpusDecoder()
    assert not d.has_data()
    assert d.size() == 0


def test_feed_and_has_data():
    d = OggOpusDecoder()
    d.feed(b"\x01\x02")
    assert d.has_data()
    assert d.size() == 2


def test_feed_empty_bytes_ignored():
    d = OggOpusDecoder()
    d.feed(b"")
    assert not d.has_data()


def test_size_accumulates():
    d = OggOpusDecoder()
    d.feed(b"aaa")
    d.feed(b"bb")
    assert d.size() == 5


def test_reset_clears_chunks():
    d = OggOpusDecoder()
    d.feed(b"hello")
    d.reset()
    assert not d.has_data()
    assert d.size() == 0


def test_drain_empty_returns_empty_bytes():
    d = OggOpusDecoder()
    result = d.drain(target_sr=16000)
    assert result == b""


def test_drain_invalid_blob_returns_empty_bytes():
    """Garbage bytes: soundfile should fail → drain returns b''."""
    d = OggOpusDecoder()
    d.feed(b"\x00" * 64)          # not a valid ogg/opus file
    result = d.drain(target_sr=16000)
    assert result == b""


def test_drain_clears_internal_state():
    """After a drain (even of invalid data) has_data() must be False."""
    d = OggOpusDecoder()
    d.feed(b"\xff\xfe" * 10)
    d.drain(target_sr=16000)
    assert not d.has_data()


def test_drain_dump_path_parent_created(tmp_path):
    """dump_path parent is created on demand; invalid blob still returns b''."""
    d = OggOpusDecoder()
    d.feed(b"\x00" * 32)
    out_path = tmp_path / "sub" / "001.ogg"
    result = d.drain(target_sr=16000, dump_path=out_path)
    assert result == b""
    # parent dir was created and the raw blob was written before decode attempt
    assert out_path.parent.exists()
