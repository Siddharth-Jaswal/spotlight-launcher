import json
import webbrowser
import subprocess

from PyQt6.QtWidgets import QWidget, QLineEdit, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication

from style import STYLE


class Launcher(QWidget):

    def __init__(self):
        super().__init__()

        with open("commands.json") as f:
            self.commands = json.load(f)

        self.setFixedSize(500, 60)

        screen = QGuiApplication.primaryScreen().geometry()

        x = (screen.width() - self.width()) // 2
        y = int(screen.height() * 0.25)

        self.move(x, y)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self.setStyleSheet(STYLE)

        self.input = QLineEdit(self)
        self.input.setGeometry(0, 0, 440, 60)

        self.input.setPlaceholderText("Search or run command...")
        self.input.returnPressed.connect(self.execute)

        # close button
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setGeometry(460, 15, 30, 30)
        self.close_btn.clicked.connect(self.hide)

        self.hide()

    def execute(self):

        cmd = self.input.text().strip().lower()

        if cmd in self.commands:

            target = self.commands[cmd]

            if target.startswith("http"):
                webbrowser.open(target)
            else:
                subprocess.Popen(target)

        self.input.clear()
        self.hide()

    def open_launcher(self):

        self.show()
        self.raise_()
        self.activateWindow()
        self.input.setFocus()

    def keyPressEvent(self, event):

        if event.key() == Qt.Key.Key_Escape:
            self.input.clear()
            self.hide()

    def mousePressEvent(self, event):
        self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = event.globalPosition().toPoint() - self.old_pos
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPosition().toPoint()