# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Doppelvoice (Windows GUI).

Build:
    .venv\\Scripts\\pyinstaller doppelvoice.spec --clean --noconfirm

Output (v0.3.0+):
    dist/Doppelvoice.exe   (single onefile bundle, ~80 MB)

设计选择：
- **onefile** since v0.3.0: 一个 .exe，开箱即用。代价是首次启动 7-10s
  （PyInstaller bootloader 把 _internal/ 解压到 %TEMP%/_MEIxxxxxx/ 再跑）。
- 数据目录走 %APPDATA%/Doppelvoice/（config.py _resolve_project_root），
  不在 .exe 同目录写 .env / logs，避免 Program Files 写权限问题。
- console=False：发布时不弹黑窗（开发期把 console=True 看 traceback）。
- 显式收集 _sounddevice_data / _soundfile_data 的 native DLL。
- 显式收集 doppelvoice.engine._pb.* 子模块（PyInstaller 漏分析 protobuf 生成代码）。
- LICENSE / THIRD_PARTY_LICENSES.md 不再内嵌（onefile 模式下用户拿不到）；
  改为 release zip 里同级摆放，下载页可见。
"""
from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)

block_cipher = None

# ── 数据 / 二进制依赖 ─────────────────────────────────────────────────────

binaries = []
# onefile 模式下数据文件嵌进 .exe 后用户拿不到，所以 LICENSE 不在 datas 里 ——
# 改在 release zip 中同级摆放（手动复制到 dist/）。
datas = []

# PortAudio：sounddevice 通过 _sounddevice_data 找 libportaudio*.dll
binaries += collect_dynamic_libs("_sounddevice_data")
datas    += collect_data_files("_sounddevice_data")

# libsndfile：soundfile 通过 _soundfile_data 找
binaries += collect_dynamic_libs("_soundfile_data")
datas    += collect_data_files("_soundfile_data")

# soxr 自带 .pyd，PyInstaller 通常自动跟踪，但 hiddenimports 加保险
# soxr_ext.pyd 在 soxr 包里，binaries 自动拣到

# ── hiddenimports：PyInstaller 静态分析跟不到的运行时 import ───────────

hiddenimports = []

# Protobuf：所有生成的 *_pb2 模块需要显式列出（因为 protocol.py 是动态找的）
hiddenimports += collect_submodules("doppelvoice.engine._pb")
# google.protobuf 的 builder 模块在 6.x 里被 *_pb2.py 通过字符串引用
hiddenimports += [
    "google.protobuf.internal.builder",
    "google.protobuf.runtime_version",
    "google.protobuf.descriptor_pool",
    "google.protobuf.symbol_database",
]
# qasync 的 platform-specific submodule
hiddenimports += ["qasync._windows"]


a = Analysis(
    ["src/doppelvoice/__main__.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 节流：用不到的大件
        "tkinter",
        "matplotlib",
        "pytest",
        "PyInstaller",
        # PySide6 webengine 一个就 200MB+，我们不需要
        "PySide6.QtWebEngine",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtMultimediaWidgets",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DRender",
        "PySide6.QtBluetooth",
        "PySide6.QtPositioning",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtSensors",
        "PySide6.QtSerialPort",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# onefile 模式：所有 binaries / datas 全部塞进单个 .exe，运行时解压到 %TEMP%
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Doppelvoice",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                 # UPX 压缩与 PySide6 经常冲突
    console=False,             # GUI 模式，不弹 cmd 窗
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    runtime_tmpdir=None,       # 默认用 %TEMP%
    # icon='docs/images/icon.ico',  # 没图标文件就先注释掉
)
