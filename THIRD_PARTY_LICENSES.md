# Third-Party Licenses

Doppelvoice itself is released under the MIT License (see [LICENSE](LICENSE)).
The bundled distribution (`Doppelvoice-vX.Y.Z-win64.zip`) ships native
binaries that are licensed under different terms. This document collects
those notices so that redistribution complies with each upstream license.

## Summary

| Library | Bundled file(s) | License | Notice link |
|---|---|---|---|
| **PySide6 / shiboken6** | `_internal/PySide6/Qt6Core.dll` and other `Qt6*.dll`, `*.pyd` | LGPL-3.0-only OR GPL-2.0 OR GPL-3.0 (LGPL chosen here) | https://doc.qt.io/qt-6/lgpl.html |
| **libsoxr** (via `soxr` Python wheel) | `_internal/soxr/soxr_ext.pyd` | LGPL-2.1-or-later | https://sourceforge.net/projects/soxr/ |
| **PortAudio** (via `sounddevice`) | `_internal/_sounddevice_data/portaudio-binaries/libportaudio64bit*.dll` | MIT-style | http://www.portaudio.com/license.html |
| **libsndfile** (via `soundfile`) | `_internal/_soundfile_data/libsndfile_x64.dll` | LGPL-2.1-or-later | https://github.com/libsndfile/libsndfile/blob/master/COPYING |
| **OpenSSL** (Python's bundled `ssl`) | `_internal/libssl-3-x64.dll`, `_internal/libcrypto-3-x64.dll` | Apache-2.0 (OpenSSL 3.x) | https://www.openssl.org/source/license.html |
| **gRPC / Protobuf runtime** | `_internal/google/protobuf/...` | Apache-2.0, BSD-3-Clause | https://github.com/protocolbuffers/protobuf/blob/main/LICENSE |
| **NumPy** | `_internal/numpy/`, `_internal/numpy.libs/` | BSD-3-Clause + bundled OpenBLAS BSD-3 | https://numpy.org/doc/stable/license.html |
| **websockets** | `_internal/websockets/` | BSD-3-Clause | https://github.com/python-websockets/websockets/blob/main/LICENSE |
| **loguru, qasync, python-dotenv** | as named | MIT / BSD-2-Clause / BSD-3-Clause | upstream repos |

All other pure-Python dependencies are MIT or BSD; their full license
text ships inside each package's `*.dist-info/` directory.

## LGPL compliance notice

Two of the bundled native libraries are LGPL: **Qt 6** (via PySide6) and
**libsoxr**. Section 4 of LGPL-3.0 / Section 6 of LGPL-2.1 require that
recipients are able to relink the program against a modified version of
the library. Because we ship them as ordinary DLL / PYD files in
`_internal/`, this requirement is satisfied: you may replace
`_internal/PySide6/Qt6*.dll`, `_internal/soxr/soxr_ext.pyd`, or
`_internal/_soundfile_data/libsndfile_x64.dll` with your own build.

The corresponding library source code is available from each project's
website linked above.

If you redistribute this binary, please keep this `THIRD_PARTY_LICENSES.md`
and the `LICENSE` file alongside it.
