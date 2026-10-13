"""Verify the shipped ZIP from a different cwd without Python/Conda in PATH."""
import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from wordsense import __version__


def main():
    root = Path(__file__).resolve().parents[1]
    release_name = f"WordSense-v{__version__}"
    archive = root / "dist" / f"{release_name}-Windows-x64.zip"
    report = root / "docs" / "extracted-smoke.json"
    with tempfile.TemporaryDirectory(prefix="WordSense 验收 ") as directory:
        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
            assert f"{release_name}/_internal/assets/wordsense.ico" in names
            assert f"{release_name}/THIRD_PARTY_NOTICES.txt" in names
            assert f"{release_name}/licenses/LGPL-3.0-only.txt" in names
            assert not any(name.casefold().endswith((".sqlite3", ".sqlite3-wal", ".sqlite3-shm"))
                           for name in bundle.namelist()), "Release must not include a user dictionary"
            bundle.extractall(directory)
        executable = Path(directory) / release_name / "WordSense.exe"
        environment = os.environ.copy()
        for key in ("PYTHONHOME", "PYTHONPATH", "QT_PLUGIN_PATH", "QML2_IMPORT_PATH"):
            environment.pop(key, None)
        system = environment.get("SystemRoot", "C:/Windows")
        environment["PATH"] = str(Path(system) / "System32") + os.pathsep + system
        environment["QT_QPA_PLATFORM"] = "windows"
        result = subprocess.run([str(executable), "--smoke-test", str(report)],
                                cwd=directory, env=environment, timeout=45, check=True)
        output = json.loads(report.read_text(encoding="utf-8"))
        assert output["status"] == "passed" and output["frozen"]
        print(json.dumps({"archive": archive.name, "relocated_with_unicode_and_spaces": True,
                          "python_removed_from_path": True, "user_dictionary_in_zip": False,
                          "logo_and_license_files_in_zip": True,
                          "exit_code": result.returncode, "report": str(report)}, indent=2))


if __name__ == "__main__":
    main()
