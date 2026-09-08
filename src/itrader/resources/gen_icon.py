"""Generate icon.png for the tray app.

Run once to produce src/itrader/resources/icon.png.
The icon is a dark rounded square with a yellow "T" (iTrader).
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication


def render(size: int = 256) -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)

    # Background rounded rect
    margin = size // 16
    bg_rect = pix.rect().adjusted(margin, margin, -margin, -margin)
    radius = size // 6
    painter.setBrush(QColor("#1e1e2e"))
    pen = QPen(QColor("#45475a"))
    pen.setWidth(max(1, size // 64))
    painter.setPen(pen)
    painter.drawRoundedRect(bg_rect, radius, radius)

    # "T" letter
    font = QFont("Helvetica Neue", int(size * 0.52))
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor("#f9e2af"))
    painter.drawText(bg_rect, Qt.AlignCenter, "T")

    painter.end()
    return pix


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    out = Path(__file__).parent / "icon.png"
    render(256).save(str(out), "PNG")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
