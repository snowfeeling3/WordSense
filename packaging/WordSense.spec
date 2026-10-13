# Build from the repository root: python -m PyInstaller packaging/WordSense.spec
from pathlib import Path
import runpy

root = Path(SPECPATH).parent
release_version = runpy.run_path(str(root / 'wordsense' / '__init__.py'))['__version__']
a = Analysis([str(root / 'launcher.py')], pathex=[str(root)],
             binaries=[], datas=[(str(root / 'assets' / 'wordsense.ico'), 'assets')], hiddenimports=[], hookspath=[], hooksconfig={},
             runtime_hooks=[], excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
                 'PySide6.QtWebEngineQuick', 'PySide6.QtPdf', 'PySide6.QtPdfWidgets'],
             noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='WordSense',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, icon=str(root / 'assets' / 'wordsense.ico'),
          version=str(root / 'packaging' / 'version_info.txt'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name=f'WordSense-v{release_version}')
