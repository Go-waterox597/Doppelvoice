"""env_io read/write/has_credentials unit tests — uses tmp_path, no real .env."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

import doppelvoice.gui.env_io as env_io


def _patch_env_path(tmp_path: Path):
    """Redirect env_io.env_path() to a temp file for isolation."""
    p = tmp_path / ".env"
    return patch.object(env_io, "env_path", return_value=p)


# ── read_env ──────────────────────────────────────────────────────────────────

def test_read_env_missing_file_returns_empty(tmp_path):
    with _patch_env_path(tmp_path):
        assert env_io.read_env() == {}


def test_read_env_parses_key_value(tmp_path):
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n", encoding="utf-8")
    with _patch_env_path(tmp_path):
        result = env_io.read_env()
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_read_env_skips_comments_and_blanks(tmp_path):
    p = tmp_path / ".env"
    p.write_text("# comment\n\nKEY=val\n", encoding="utf-8")
    with _patch_env_path(tmp_path):
        assert env_io.read_env() == {"KEY": "val"}


def test_read_env_strips_quotes(tmp_path):
    p = tmp_path / ".env"
    p.write_text('A="hello"\nB=\'world\'\n', encoding="utf-8")
    with _patch_env_path(tmp_path):
        result = env_io.read_env()
    assert result["A"] == "hello"
    assert result["B"] == "world"


# ── write_env ─────────────────────────────────────────────────────────────────

def test_write_env_creates_file(tmp_path):
    with _patch_env_path(tmp_path):
        env_io.write_env({"X": "1"})
    assert (tmp_path / ".env").exists()


def test_write_env_roundtrip(tmp_path):
    with _patch_env_path(tmp_path):
        env_io.write_env({"DOUBAO_APP_KEY": "mykey", "DOUBAO_ACCESS_KEY": "mysecret"})
        result = env_io.read_env()
    assert result["DOUBAO_APP_KEY"] == "mykey"
    assert result["DOUBAO_ACCESS_KEY"] == "mysecret"


def test_write_env_preserves_unknown_keys(tmp_path):
    p = tmp_path / ".env"
    p.write_text("EXISTING=old\nDOUBAO_APP_KEY=x\n", encoding="utf-8")
    with _patch_env_path(tmp_path):
        env_io.write_env({"DOUBAO_APP_KEY": "new"}, preserve_unknown=True)
        result = env_io.read_env()
    assert result["EXISTING"] == "old"
    assert result["DOUBAO_APP_KEY"] == "new"


def test_write_env_no_preserve_drops_unknown(tmp_path):
    p = tmp_path / ".env"
    p.write_text("EXISTING=old\n", encoding="utf-8")
    with _patch_env_path(tmp_path):
        env_io.write_env({"ONLY_NEW": "1"}, preserve_unknown=False)
        result = env_io.read_env()
    assert "EXISTING" not in result
    assert result["ONLY_NEW"] == "1"


# ── has_credentials ───────────────────────────────────────────────────────────

def test_has_credentials_false_when_no_file(tmp_path):
    with _patch_env_path(tmp_path):
        assert env_io.has_credentials() is False


def test_has_credentials_false_when_keys_empty(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DOUBAO_APP_KEY=\nDOUBAO_ACCESS_KEY=\n", encoding="utf-8")
    with _patch_env_path(tmp_path):
        assert env_io.has_credentials() is False


def test_has_credentials_true_when_both_present(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DOUBAO_APP_KEY=ak\nDOUBAO_ACCESS_KEY=sk\n", encoding="utf-8")
    with _patch_env_path(tmp_path):
        assert env_io.has_credentials() is True


# ── _dequote (v0.2.3 fix: align with python-dotenv) ────────────────────────────

def test_dequote_matched_double():
    assert env_io._dequote('"hello"') == "hello"


def test_dequote_matched_single():
    assert env_io._dequote("'hello'") == "hello"


def test_dequote_unmatched_keeps_chars():
    """Old behavior was to greedily strip both quote types — wrong."""
    # `"'weird'"` has matched outer ", inner '. dotenv strips ONLY the outer pair.
    assert env_io._dequote("\"'weird'\"") == "'weird'"


def test_dequote_preserves_inner_padding():
    """Old `.strip().strip('"')` exposed inner spaces; dotenv preserves them."""
    assert env_io._dequote('"  spaced  "') == "  spaced  "


def test_read_env_handles_utf8_bom(tmp_path):
    """v0.2.2 fix: Notepad's default UTF-8 BOM should not corrupt key names."""
    p = tmp_path / ".env"
    # Write with explicit BOM
    p.write_bytes(b"\xef\xbb\xbfDOUBAO_APP_KEY=value\n")
    with _patch_env_path(tmp_path):
        result = env_io.read_env()
    assert "DOUBAO_APP_KEY" in result  # NOT "\ufeffDOUBAO_APP_KEY"
    assert result["DOUBAO_APP_KEY"] == "value"
