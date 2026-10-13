"""PyInstaller entry point; source runs use python -m wordsense."""
from wordsense.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
