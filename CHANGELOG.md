# Changelog

All notable changes to Doppelvoice will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.2] - 2026-04-26

20-agent adversarial sweep (architect / security / performance / Python /
code-review / refactor / docs / tdd / first-install UX / 24h stability /
cross-platform / dep audit / concurrency / WS protocol / audio math /
error UX / dist UX / i18n / malicious-server / .env edges). 86 tests
(was 46) — coverage 14% → 24%. **No public API changes.**

### Fixed
- **CRITICAL** `audio/capture.py` referenced `_HAS_SOXR` without importing
  it — `NameError` on every sample-rate-mismatch path, silently breaking
  capture when the device's native rate ≠ 16 kHz.
- **CRITICAL** `audio/opus_decoder.py` had **unbounded `_chunks` growth**
  when the server emitted `TTSSentenceStart` without ever sending
  `TTSSentenceEnd` (malicious or stuck server). Now hard-capped at 64 MB
  with a warning + drop. `size()` is O(1) (cached).
- **CRITICAL** `gui/env_io.py` opened `.env` as `utf-8` strict — Windows
  Notepad's default "UTF-8" save adds a BOM, which made the GUI think
  it had loaded a key named `"\ufeffDOUBAO_APP_KEY"` while runtime got
  none. Now uses `utf-8-sig` to strip the BOM transparently.
- **HIGH** `utils/log.py` `_KV_PATTERN` could not redact bare-keyword
  fields like `password=`, `secret=`, `token=` because the leading
  `[A-Za-z]` always consumed the first character — by the time the
  regex engine tried to match the keyword, it was already past `p`.
  Made the prefix optional.
- **HIGH** `gui/main_window.py` status badge displayed the literal string
  `"status.busy"` after a language switch because `_apply_translations`
  reverse-looked up the i18n key from the mapped state value
  (`busy`/`running`/`error`) instead of the original key (`connecting`,
  `opening_audio`, etc.). Now stores the original key as a Qt property
  and reads that on language change.
- **HIGH** `audio/resample.py` linear fallback returned the **input
  array** unchanged when `n_out == 0` (very short buffer + heavy
  downsample) — downstream consumed it at the wrong sample rate without
  any error. Now returns an empty `int16` array.
- **HIGH** `pipeline/orchestrator.py` reconnect counter only reset after
  `_one_session()` ran to completion. Reflective WiFi flapping
  (5+ short drops before any session stabilized) caused exponential
  backoff to climb to the 30-second cap, locking the user out of audio
  for 30s at a time. Now resets the counter as soon as `SessionStarted`
  is acknowledged — i.e., once the session is "stable", any subsequent
  drop counts as a fresh attempt #1.
- **HIGH** `gui/main_window.py` `closeEvent` did not stop
  `_metrics_timer` first, leaving a 150 ms window where `_tick_metrics`
  could read `orchestrator.capture` after `capture.stop()` had run.
- **HIGH** `gui/main_window.py` Settings menu (Ctrl+,) was **not**
  disabled while a session was running, so users could change `chunk_ms`
  / `output_format` / etc. mid-session and watch a "saved" toast appear
  while the running orchestrator (which holds an immutable `snapshot()`)
  silently ignored the change. Now `act_settings` is gated like the
  toolbar Settings button.
- **MEDIUM** `cli.py` help text for `--jitter-ms` said "默认 240" but the
  actual default has been 120 since v0.2.0.

### Added
- **`__post_init__` validation** on `AudioConfig` and `NetworkConfig`:
  catches negative / zero `chunk_ms`, `input_sample_rate`, `channels`
  not in `(1, 2)`, etc., at construction time with a clear `ValueError`
  instead of letting PortAudio surface a cryptic `-9997` 200 ms later.
- **VB-Cable startup pre-check** in `gui/app.py`: if no `CABLE Input`
  output device is found, the (already-translated) "Virtual audio
  device missing" dialog now actually fires. Previously the i18n keys
  existed but were never wired up.
- **`THIRD_PARTY_LICENSES.md`**: enumerates every bundled native
  library and its license. PyInstaller spec now copies `LICENSE` and
  `THIRD_PARTY_LICENSES.md` into `dist/Doppelvoice/` so end-users
  receive LGPL-required notices for PySide6 (Qt 6), libsoxr, and
  libsndfile alongside the binary.
- **Bilingual `.env.example`** with explicit "App Key vs Access Token"
  guidance — first-install UX review confirmed users routinely swap
  the two fields.
- **Lazy log formatting** in `audio/capture.py`: `logger.debug("...{}",
  status)` instead of f-string. f-strings eager-evaluate even when the
  level is filtered, costing ~1-2% CPU on a 12.5 Hz audio callback.

### Changed
- `requirements.txt` now pins **upper bounds** (`numpy<3`,
  `websockets<17`, `protobuf<7`, `soxr<2`, `PySide6<7`) plus the new
  `soundfile` dep that was implicit before. `grpcio-tools` removed
  from runtime deps (it's only needed to regenerate `*_pb2.py` from
  `.proto`); already in `[project.optional-dependencies].dev`.
- `gui/i18n.py`: removed 11 dead translation keys (`wizard.*` (7),
  `config.mode`, `stats.latency`, `stats.buffer`, `settings.api.show_secret`).
  Wizard never had a class wiring them; the others were stat labels
  the GUI never displayed. Added `device.tooltip.backend` and switched
  the device-list tooltip from hardcoded "后端" to the i18n key.
- `gui/bus.py`: removed `metrics` and `usage` signals — declared but
  never connected to any slot.
- `gui/widgets/status_badge.py`: removed unused `_state` attribute.
- `pyproject.toml` / `__init__.py` bumped to `0.2.2`.

### Tests
- New: `tests/test_env_io.py` (read/write atomic env), `tests/test_opus_decoder.py`
  (feed/drain/reset/empty/garbage), `tests/test_orchestrator_units.py`
  (`_drain_queue`, `_handle_*` handlers, `_FatalRemote`).
- Expanded: `tests/test_doubao_classify.py` adds `_validate_ws_url` allowlist
  cases; `tests/test_config.py` adds `AppConfig.load` env-var override
  matrix.
- 46 → **86 tests**, coverage 14% → 24%. (GUI modules remain at 0% —
  Qt requires `pytest-qt` + an offscreen platform plugin to test.)

### Known limits not yet fixed (deferred — see review reports for owner ↔ ROI)
- **OpenSSL 3.2.4 in bundle** has CVE-2024-12797 (HIGH, raw-public-key
  TLS bypass — not exploitable in our use of cert-based WSS, but the
  DLLs are still old). Will be picked up automatically on next Python
  3.12.x point release.
- 24-hour memory growth via `SubtitleView`'s 2000-block FIFO and
  PySide6 layout cache — irrelevant for typical meeting sessions.
- Voice-clone "tone shift" on every reconnect (server re-samples
  zero-shot voice profile per session). Pending Doubao API research.

## [0.2.1] - 2026-04-26

Metadata + tooling clean-up surfaced by post-release audit.

### Fixed
- `pyproject.toml` was missing 4 required dependencies (`PySide6`, `protobuf`,
  `qasync`, `soundfile`) — `pip install .` produced an unrunnable install.
  Now matches `requirements.txt`. Heavy dev-only deps (`grpcio-tools`,
  `pyinstaller`) split into `[project.optional-dependencies].dev`.
- Version drift across files:
  - `pyproject.toml` `version` `0.1.0` → `0.2.1`
  - `src/doppelvoice/__init__.py` `__version__` `0.1.0` → `0.2.1`
- `LICENSE` copyright line said "tongchuan contributors" (the pre-rename
  project name). Now reads "Doppelvoice contributors".
- `pyproject.toml` description was Chinese-only and still claimed "中→英".
  Replaced with bilingual-aware English description that correctly lists
  all 9 supported languages.

### Added
- GitHub Actions CI (`.github/workflows/tests.yml`): pytest matrix on
  Windows / Python 3.10 / 3.11 / 3.12 with coverage report upload.
- `pyproject.toml` now declares `keywords`, `classifiers`, `urls`, and
  `readme` for proper PyPI / package-index display.
- README (en + zh) now documents the **pre-built binary** install path
  alongside the from-source path. Real CI badge replaces the static fake
  one. Added a `Release` shield linking to the latest GitHub release.

## [0.2.0] - 2026-04-26

Major code-review sweep: 4 parallel agent reviews (architecture / Python /
security / performance) drove a 24-file overhaul. Tests grew 3 → 46.

### Added
- **9-language translation support** per official Doubao spec (doc 1756902):
  `zh / en / ja / id / es / pt / de / fr / zhen`. `zhen` is the bilingual
  ZH⇄EN auto mode (source and target both set to `zhen`).
- **Voice clone tuning**: explicit `denoise=false` in `TranslateRequest` (proto
  field 7) to retain breath / resonance details that the server's default
  denoise pass would otherwise flatten. Tunable via `DENOISE` env var or the
  Settings dialog Advanced tab.
- **Audio device deduplication**: `list_unique_devices()` collapses one
  physical device's MME / DirectSound / WASAPI / WDM-KS duplicates into a
  single entry, with MME's 31-character name truncation handled. Best host
  API is chosen automatically (input → MME / DirectSound for sample-rate
  flexibility; output → WASAPI for low latency).
- **Subtitle memory cap** (`MAX_BLOCKS=2000`) so long sessions don't grow the
  `QTextDocument` unbounded.
- **Atomic `.env` write**: `tempfile.mkstemp` + `os.fsync` + `os.replace`
  prevents credential loss if the process crashes mid-write.
- **Log redaction patcher** (`utils/log.py`): every record passes through a
  3-stage scrubber (KV pairs / `Bearer` tokens / orphan high-entropy strings)
  before reaching stderr or files. Plus `safe_error_message()` for UI use.
- **WebSocket URL allowlist** + 64 MB → 4 MB frame size guard +
  `ParseFromString` length check before deserialization.
- **AppConfig snapshot** isolation: `Orchestrator` takes `cfg.snapshot()` at
  construction; `SettingsDialog` mutations only affect the next session.
- **Tests** (3 → 46): `test_resample`, `test_devices` (with mock host APIs),
  `test_doubao_classify` (every event branch), `test_log_redact`,
  `test_config` (frozen + snapshot semantics).

### Changed
- `AudioConfig` / `TranslationConfig` / `NetworkConfig` now `@dataclass(frozen=True)`.
  External writes go through `dataclasses.replace(cfg.audio, …)` and assignment
  back to `cfg.audio`.
- `silence_rms_threshold` default `0.010` → **`0.0`**. The old default was
  silently dropping the first 80 ms of quiet speech onsets, adding 300–500 ms
  to first-word latency; the server has its own VAD anyway.
- Mic level meter is no longer a second `sd.InputStream`. `MicCapture` now
  exposes `peak_level` from inside its existing audio callback; the GUI polls
  it from the metrics timer. One physical mic = one PortAudio stream.
- `_receiver_loop` split into `_handle_audio` / `_handle_sentence` /
  `_handle_subtitle` / `_handle_error` plus a `_ReceiverContext` dataclass
  for state. The 80-line nested `if/elif` is gone.
- `_resample` extracted to `audio/resample.py` (was duplicated across
  `capture.py` / `playback.py`, with `opus_decoder.py` doing a circular
  `from doppelvoice.audio.capture import _resample`).
- `send_audio()` reuses a cached `TranslateRequest` template (12 protobuf
  object allocations per second saved).
- `playback._callback` writes directly into the ctypes `outdata` buffer
  instead of constructing an intermediate `bytes(...)` copy under the lock.
- `closeEvent` guards against double-confirm via `_quitting` flag and uses
  `asyncio.get_running_loop()` instead of the deprecated `get_event_loop()`.
- `i18n.detect_system_language()` migrated from deprecated
  `locale.getdefaultlocale()` to `locale.getlocale()`.

### Fixed
- **Generated protobuf imports rewritten to absolute paths**
  (`from doppelvoice.engine._pb.common import …`). The `sys.path.insert(_pb)`
  hack in `protocol.py` is gone, eliminating a PyInstaller-onefile blocker
  and avoiding `sys.modules` pollution under top-level names `common` /
  `products`.
- Several `except Exception: pass` swallows replaced with
  `logger.debug(..., exc_info=True)` so audio / WebSocket failures stop being
  invisible.
- `settings_dialog._on_test_connection` no longer leaks raw exception
  tracebacks (which can carry server-echoed credentials) to log files; the
  message is funneled through `safe_error_message`.
- `closeEvent` no longer prompts twice if the user clicks ✕ a second time
  while graceful shutdown is in progress.

### Documented
- README + docs updated for 9 languages and `DENOISE` env var.
- `docs/zh/ARCHITECTURE.md` rewritten (was still describing the pre-rename
  `client/` layout and the 24 kHz / `pcm` settings that no longer apply).
- `TROUBLESHOOTING.md` (zh + en) updated with the acoustic-feedback-loop
  diagnosis (speakers → mic re-capture → re-translation back to the peer)
  and the cure (use headphones).

## [0.1.1] - 2026-04-25

### Changed
- Project renamed from `tongchuan` to `Doppelvoice`
- Package directory restructured: `client/` → `engine/`, `pb/` → `_pb/`
- Examples (`probe_*.py`) moved to `examples/`
- Documentation split into `docs/zh/` and `docs/en/`

### Added
- Bilingual README (English + 简体中文)
- `docs/en/`: full English translation of PRD, ARCHITECTURE, SETUP, TROUBLESHOOTING
- `docs/zh/TROUBLESHOOTING.md`
- `CHANGELOG.md`, `CODE_OF_CONDUCT.md`

## [0.1.0] - 2026-04-22

First working release.

### Added
- End-to-end Chinese → English real-time translation via Doubao Seed AST 2.0
- Zero-shot voice cloning (per-session, model-driven)
- PySide6 GUI with live bilingual subtitles, device picker, jitter / RMS controls
- CLI mode (`--check`, `--list-devices`, `--gui`)
- Automatic reconnect with exponential backoff
- Fatal-vs-transient error classification
- Multi-rate audio capture fallback (WASAPI 16 kHz issue workaround)
- ogg_opus per-sentence decoder (libsndfile-backed)
- Privacy-by-default: no audio or subtitle persistence unless `DUMP_AUDIO=1`
- GitHub Actions CI (Windows, Python 3.10/3.11/3.12)

### Fixed
- 4 HIGH and 3 MEDIUM issues from external code review:
  - `SessionCanceled(151)` event handling
  - sender/receiver task cancellation race
  - close-window cleanup not awaiting `run_task`
  - `Billing` field parsing in `UsageResponse`
- 8 HIGH and 2 MEDIUM issues from earlier review:
  - `iter_events` swallowing `ConnectionClosed`
  - capture queue not draining across reconnects
  - playback state not flushing across reconnects
  - audio callback thread → asyncio loop boundary safety
  - PortAudio stream lifecycle on shutdown
  - request_meta required-field gaps in `TaskRequest` / `FinishSession`
- Audio playback bug: `_max_buf_bytes` cap was too small for sentence-mode opus, truncating long sentences to ~360 ms

### Tuned
- `output_sample_rate` default 24 kHz → 48 kHz (fullband, more natural prosody)
- `format` field aligned with official `ast_demo.py`: `"pcm"` → `"wav"`
- Removed denoise / platform fields that were dead options
- chunk size 60 ms → 80 ms (matches Doubao recommendation)
- jitter buffer 240 ms → 120 ms (lower latency)
- `find_device` for input prefers MME / DirectSound (16 kHz support); WASAPI for output (low latency)
