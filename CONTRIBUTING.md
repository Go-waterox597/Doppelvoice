# Contributing

Thanks for considering a contribution!

## Setup

```cmd
git clone https://github.com/TianqBu/Doppelvoice.git
cd Doppelvoice
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"     :: installs runtime + dev (pytest, pyinstaller, etc.)
```

Copy `.env.example` to `.env` and fill in your Doubao credentials.

## Run tests

```cmd
.venv\Scripts\python -m pytest tests/ -v
```

Coverage:

```cmd
.venv\Scripts\python -m pytest tests/ --cov=doppelvoice --cov-report=term-missing
```

The `examples/probe_*.py` scripts are interactive E2E probes that hit the live API and need a working microphone (and credentials).

## Coding style

- Python 3.10+
- Type hints on public APIs
- Sub-configs (`AudioConfig` / `TranslationConfig` / `NetworkConfig`) are `@dataclass(frozen=True)`. Mutate via `dataclasses.replace(cfg.audio, …)` and assign back to `cfg.audio` — never `cfg.audio.field = x`.
- Docstrings only when behaviour isn't obvious; comments only when WHY isn't obvious
- Keep modules under ~400 lines

## Pull requests

1. Open an issue first if it's a non-trivial change
2. Branch off `main`
3. Keep commits focused; bundle related changes
4. Make sure `pytest tests/` passes (CI will also run on push)
5. For protocol changes: regenerate the protobuf bindings (see `src/doppelvoice/engine/protos/`) and rewrite the generated `from common import` / `from products import` lines to absolute paths (`from doppelvoice.engine._pb.common import …`) — see `protocol.py` for the rationale

## Reporting issues

Please include:
- Windows version (`winver`)
- Python version (`python --version`) — or note "using bundled .exe"
- Audio device names (output of `Doppelvoice.exe --list-devices` or `run.bat --list-devices`)
- Relevant log excerpt from `logs/doppelvoice_*.log` (logs auto-redact API keys but double-check before sharing)
- Source / target language, mic make/model

## Areas open for contribution

- macOS / Linux ports (replace VB-Cable with BlackHole / PipeWire)
- Streaming opus decode (currently waits for full sentence; would cut ~3s output latency — see `audio/opus_decoder.py`)
- Push-to-talk hotkey (workaround for the speakers-feedback-loop case)
- WebRTC AEC3 integration (full echo cancellation; needs far-end signal capture)
- Subtitle overlay window (always-on-top transparent)
- System tray controls
- More languages once Doubao adds them (currently 9 supported)
