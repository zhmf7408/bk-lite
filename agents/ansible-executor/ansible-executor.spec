# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_all, copy_metadata


COLLECTIONS_ROOT = Path("build/pyinstaller-collections").resolve()
ANSIBLE_WINDOWS_ROOT = (
    COLLECTIONS_ROOT / "ansible_collections" / "ansible" / "windows"
)

if not ANSIBLE_WINDOWS_ROOT.exists():
    raise SystemExit(
        "Missing ansible.windows collection under build/pyinstaller-collections. "
        "Run 'make package' so the collection is installed before PyInstaller builds the binary."
    )

ansible_datas, ansible_binaries, ansible_hiddenimports = collect_all("ansible")
ansible_windows_datas = Tree(
    str(ANSIBLE_WINDOWS_ROOT),
    prefix="collections/ansible_collections/ansible/windows",
    excludes=["*.pyc", "__pycache__"],
)

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=ansible_binaries,
    datas=ansible_datas
    + copy_metadata("ansible-core")
    + copy_metadata("jinja2")
    + [("config.example.yml", ".")]
    + ansible_windows_datas,
    hiddenimports=ansible_hiddenimports + ["nats.aio.client"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    module_collection_mode={"ansible": "py+pyz"},
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ansible-executor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ansible-executor",
)
