# Setup & Usage

[中文](../zh/SETUP.md)

Two install paths. **Path A** is fastest (no Python install, GUI handles
everything). **Path B** is for developers who want to run from source.

---

## Path A — Pre-built binary (recommended)

### A.1. Install VB-Audio Virtual Cable (free, required)

1. Download: https://vb-audio.com/Cable/ → click **Download** → unzip
2. **Right-click** `VBCABLE_Setup_x64.exe` → **Run as administrator** → click **Install Driver**
3. **Reboot** (required)
4. After reboot, verify in Windows Sound settings:
   - Output: `CABLE Input (VB-Audio Virtual Cable)`
   - Input: `CABLE Output (VB-Audio Virtual Cable)`

If you forget this step, Doppelvoice will detect it and pop a "Download
VB-Cable" button on first launch.

### A.2. Download Doppelvoice

1. Open the [latest release](https://github.com/TianqBu/Doppelvoice/releases/latest).
2. Download `Doppelvoice-vX.Y.Z-win64.zip` (~60 MB).
3. Unzip anywhere you can write to (`Downloads\`, `Desktop\`, etc.).

### A.3. Launch + configure

1. **Double-click `Doppelvoice.exe`.** First launch takes 7–10 s while
   the bundle unpacks to `%TEMP%`; subsequent launches are similar.
2. Settings dialog opens automatically. Fill in:
   - `DOUBAO_APP_KEY` = the **App Key** field in [Volcengine Console](https://console.volcengine.com/speech/app)
     (NOT Access Token / API Key — easy to confuse).
   - `DOUBAO_ACCESS_KEY` = the **Access Token** field.
   - `DOUBAO_RESOURCE_ID` is pre-filled — leave as-is.
3. Click **Test connection** to verify, then **Save**. The credentials
   land in `%APPDATA%\Doppelvoice\.env` via atomic write.

That's it — no manual file editing needed.

---

## Path B — From source (developers)

### B.1. Install Python 3.10+

Download from https://www.python.org/downloads/. Tick **Add to PATH** during install.

```cmd
python --version
```

### B.2. Install VB-Audio Virtual Cable — same as A.1.

### B.3. Install Doppelvoice from source

```cmd
git clone https://github.com/TianqBu/Doppelvoice.git
cd Doppelvoice
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
```

(`[dev]` extras include pytest + pyinstaller; omit for a runtime-only install.)

### B.4. Configure credentials

Copy `.env.example` to `.env` (in the repo root) and fill in:

```env
DOUBAO_APP_KEY=your_app_key
DOUBAO_ACCESS_KEY=your_access_token
DOUBAO_RESOURCE_ID=volc.service_type.10053

# Optional ────
# Pick from 9 codes: zh / en / ja / id / es / pt / de / fr / zhen
# zhen = bilingual ZH⇄EN auto mode; set both source and target to zhen.
SOURCE_LANG=zh
TARGET_LANG=en

# Server-side denoise: 0=off (default; preserves voice detail for cloning) / 1=on
DENOISE=0
```

### B.5. Self-check

```cmd
.venv\Scripts\activate
python -m doppelvoice --check
```

Expected:
- A list of audio devices, including `CABLE Input`
- API connectivity: PASS

### B.6. Launch

```cmd
python -m doppelvoice          :: CLI mode
python -m doppelvoice --gui    :: GUI mode
gui.bat                        :: convenience wrapper for --gui
```

---

## Use it inside meeting apps

### Zoom
1. Settings → Audio → Microphone → pick `CABLE Output (VB-Audio Virtual Cable)`.
   ("Output" sounds wrong — that's correct: it's the output of the
   virtual cable feeding INTO Zoom.)
2. Uncheck "Automatically adjust microphone volume".
3. Test call: speak the configured source language, peer hears the target.

### 腾讯会议 / 飞书 / Microsoft Teams / Google Meet (Chrome)
Same pattern: Audio settings → Microphone → `CABLE Output`.

### OBS livestream
Add an "Audio Input Capture" source → pick `CABLE Output`.

---

## Recommended hardware

- Wear a **wired or Bluetooth headset** so the mic doesn't pick up the
  speaker output (would cause a feedback loop where the peer hears
  their own voice translated back — see TROUBLESHOOTING.md).
- Or: speakers and mic on **physically separate devices**.
- Windows Sound Control Panel → Microphone properties → Levels = 80;
  **disable** noise suppression enhancements (Doubao does its own).

---

## FAQ

**Q: "Cannot find CABLE Input device"**
A: VB-Cable not installed or system not rebooted. Open `Control Panel
→ Sound → Playback` and check that `CABLE Input` is listed. Doppelvoice's
startup dialog also offers a one-click download button.

**Q: Peer says "your voice is choppy"**
A: Increase the GUI's jitter-buffer slider to 300–500 ms; or check your
network; or reduce chunk size to 60 ms.

**Q: Latency feels > 5 s**
A: Two metrics in the log's `[metrics]` line:
- High network latency → connectivity to ByteDance's data centre is slow.
- Playback queue depth growing → consumer slower than producer; reduce jitter.

**Q: How do I switch language pair?**
A: In the GUI's source/target dropdowns, or set `SOURCE_LANG` /
`TARGET_LANG` in `.env`. For bilingual ZH⇄EN auto, set **both** to `zhen`.

**Q: Voice cloning doesn't sound like me**
A:
1. Wear a wideband mic (avoid Bluetooth HFP); 10 cm or closer to your mouth.
2. Speak continuously for the first 10–15 s so the model can sample your voice.
3. Confirm `DENOISE=0` (default). Server-side denoise flattens the voice
   details the cloning model needs.
4. The Volcengine Console demo uses a separate BFF endpoint with extra
   prosody — the public API has a hard ceiling below it.

**Q: Stream drops mid-call**
A: The orchestrator auto-reconnects with exponential backoff. Frequent
drops usually mean a Volcengine API quota/QPS limit.

**Q: Peer hears their own voice translated back**
A: You're on speakers — acoustic feedback loop. Use headphones.
Details in [TROUBLESHOOTING.md → Feedback loop when using speakers](TROUBLESHOOTING.md#feedback-loop-when-using-speakers).
