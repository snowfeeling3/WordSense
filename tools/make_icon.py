"""Convert the generated PNG into a Windows ICO with seven PNG image sizes."""
import struct
from pathlib import Path
from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage


def main():
    directory = Path(__file__).resolve().parents[1] / "assets"
    original = QImage(str(directory / "wordsense-logo.png"))
    if original.isNull():
        raise RuntimeError("Logo PNG missing or invalid")
    sizes = (16, 24, 32, 48, 64, 128, 256)
    payloads = []
    for size in sizes:
        image = original.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)
        payload = QByteArray()
        buffer = QBuffer(payload)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        if not image.save(buffer, "PNG"):
            raise RuntimeError("PNG encoding failed")
        payloads.append(bytes(payload))
    offset = 6 + 16 * len(sizes)
    entries = []
    for size, payload in zip(sizes, payloads):
        entries.append(struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0,
                                   1, 32, len(payload), offset))
        offset += len(payload)
    (directory / "wordsense.ico").write_bytes(
        struct.pack("<HHH", 0, 1, len(sizes)) + b"".join(entries) + b"".join(payloads))
    print("assets/wordsense.ico: " + ", ".join(str(size) for size in sizes))


if __name__ == "__main__":
    main()
