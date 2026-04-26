"""配置 frozen + snapshot + AppConfig.load env-var 覆盖 单元测试。"""
from __future__ import annotations

import os
from dataclasses import FrozenInstanceError, replace
from unittest.mock import patch

import pytest

from doppelvoice.config import (
    AppConfig,
    AudioConfig,
    Credentials,
    NetworkConfig,
    TranslationConfig,
)


def test_audio_config_is_frozen():
    a = AudioConfig()
    with pytest.raises(FrozenInstanceError):
        a.chunk_ms = 100  # type: ignore[misc]


def test_translation_config_is_frozen():
    t = TranslationConfig()
    with pytest.raises(FrozenInstanceError):
        t.source_language = "ja"  # type: ignore[misc]


def test_network_config_is_frozen():
    n = NetworkConfig()
    with pytest.raises(FrozenInstanceError):
        n.connect_timeout_s = 5.0  # type: ignore[misc]


def test_replace_returns_independent_copy():
    a = AudioConfig(chunk_ms=80)
    b = replace(a, chunk_ms=160)
    assert a.chunk_ms == 80
    assert b.chunk_ms == 160


def test_appconfig_audio_swap():
    """AppConfig 仍可变 → 可以原子换整个 audio 引用。"""
    cfg = AppConfig(credentials=Credentials("k", "s"))
    old = cfg.audio
    cfg.audio = replace(cfg.audio, chunk_ms=200)
    assert old.chunk_ms == 80  # 原引用未变
    assert cfg.audio.chunk_ms == 200


def test_snapshot_isolates_subsequent_swaps():
    """snapshot() 拿到副本后，原 cfg 的 audio swap 不应污染快照。"""
    cfg = AppConfig(credentials=Credentials("k", "s"))
    snap = cfg.snapshot()
    cfg.audio = replace(cfg.audio, chunk_ms=999)
    assert snap.audio.chunk_ms == 80  # 快照保持
    assert cfg.audio.chunk_ms == 999


def test_credentials_is_frozen():
    """v0.2.3：Credentials 也改 frozen，防止 snapshot 后的就地修改污染会话。
    覆写必须走 dataclasses.replace。"""
    c = Credentials(app_key="x", access_key="y")
    with pytest.raises(FrozenInstanceError):
        c.app_key = "z"  # type: ignore[misc]
    # replace 路径仍可用
    c2 = replace(c, app_key="z")
    assert c2.app_key == "z"
    assert c.app_key == "x"  # 原对象不变


def test_default_denoise_is_false():
    """B-perf #denoise：克隆音色保留默认行为。"""
    t = TranslationConfig()
    assert t.denoise is False


def test_default_silence_threshold_is_zero():
    """B-perf #silence：默认关闭客户端 VAD。"""
    a = AudioConfig()
    assert a.silence_rms_threshold == 0.0


# ── AppConfig.load env-var overrides (config.py lines 118-149) ───────────────

def _fake_credentials():
    return Credentials(app_key="k", access_key="s")


def _make_load_env(monkeypatch, extra_env: dict):
    """Patch Credentials.from_env and os.getenv so AppConfig.load is testable."""
    monkeypatch.setattr(
        "doppelvoice.config.Credentials.from_env",
        staticmethod(_fake_credentials),
    )
    env = {
        "DOUBAO_APP_KEY": "k",
        "DOUBAO_ACCESS_KEY": "s",
        **extra_env,
    }
    monkeypatch.setattr("doppelvoice.config.load_dotenv", lambda *a, **kw: None)
    for key, val in env.items():
        monkeypatch.setenv(key, val)


def test_load_source_lang_override(monkeypatch):
    _make_load_env(monkeypatch, {"SOURCE_LANG": "ja"})
    cfg = AppConfig.load()
    assert cfg.translation.source_language == "ja"


def test_load_target_lang_override(monkeypatch):
    _make_load_env(monkeypatch, {"TARGET_LANG": "fr"})
    cfg = AppConfig.load()
    assert cfg.translation.target_language == "fr"


def test_load_denoise_true_from_env(monkeypatch):
    _make_load_env(monkeypatch, {"DENOISE": "true"})
    cfg = AppConfig.load()
    assert cfg.translation.denoise is True


def test_load_denoise_false_from_env(monkeypatch):
    _make_load_env(monkeypatch, {"DENOISE": "0"})
    cfg = AppConfig.load()
    assert cfg.translation.denoise is False


def test_load_dump_audio_flag(monkeypatch):
    _make_load_env(monkeypatch, {"DUMP_AUDIO": "1"})
    cfg = AppConfig.load()
    assert cfg.dump_audio_to_disk is True


def test_load_no_overrides_uses_defaults(monkeypatch):
    _make_load_env(monkeypatch, {})
    cfg = AppConfig.load()
    assert cfg.translation.source_language == "zh"
    assert cfg.translation.target_language == "en"
    assert cfg.dump_audio_to_disk is False
