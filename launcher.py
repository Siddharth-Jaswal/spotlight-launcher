import json
import os
import subprocess
import webbrowser
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication, QListWidget, QLineEdit, QPushButton, QWidget
from rapidfuzz import process

from style import STYLE


class Launcher(QWidget):
    def __init__(self, on_exit: Callable[[], None] | None = None):
        super().__init__()
        self.on_exit = on_exit
        self._processes: list[subprocess.Popen] = []

        with open("commands.json", encoding="utf-8") as f:
            self.commands = json.load(f)

        self.setFixedSize(500, 60)

        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = int(screen.height() * 0.25)
        self.move(x, y)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet(STYLE)

        self.min_btn = QPushButton("-", self)
        self.min_btn.setGeometry(430, 15, 25, 30)
        self.min_btn.clicked.connect(self.hide_launcher)

        self.close_btn = QPushButton("X", self)
        self.close_btn.setGeometry(460, 15, 30, 30)
        self.close_btn.clicked.connect(self.exit_app)

        self.input = QLineEdit(self)
        self.input.setGeometry(0, 0, 440, 60)
        self.input.setPlaceholderText("Search or run command...")
        self.input.returnPressed.connect(self.execute)

        self.list = QListWidget(self)
        self.list.setGeometry(0, 60, 500, 150)
        self.list.hide()

        self.input.textChanged.connect(self.update_suggestions)
        self.list.itemClicked.connect(self.launch_selected)

        self.hide()

    def mousePressEvent(self, event):
        self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = event.globalPosition().toPoint() - self.old_pos
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPosition().toPoint()

    def open_launcher(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.input.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide_launcher()
            return
        super().keyPressEvent(event)

    def update_suggestions(self, text):
        if not text:
            self.list.hide()
            return

        matches = process.extract(text, self.commands.keys(), limit=5)
        self.list.clear()

        for match in matches:
            self.list.addItem(match[0])

        self.list.show()

    def launch_selected(self, item):
        cmd = item.text()
        target = self.commands[cmd]
        self._launch_target(target)

        self.input.clear()
        self.list.hide()
        self.hide()

    def execute(self):
        cmd = self.input.text().strip().lower()

        if cmd not in self.commands and self.list.count() > 0:
            cmd = self.list.item(0).text()

        if cmd in self.commands:
            target = self.commands[cmd]
            self._launch_target(target)

        self.input.clear()
        self.list.hide()
        self.hide()

    def hide_launcher(self):
        self.input.clear()
        self.list.hide()
        self.hide()

    def _launch_target(self, target: str):
        if target.startswith("http"):
            webbrowser.open(target)
            return

        proc = subprocess.Popen(target)
        self._processes.append(proc)

    def shutdown_processes(self):
        running = [proc for proc in self._processes if proc.poll() is None]

        for proc in running:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    check=False,
                    capture_output=True,
                )
            else:
                proc.terminate()

        for proc in running:
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()

        self._processes.clear()

    def exit_app(self):
        self.shutdown_processes()

        if callable(self.on_exit):
            self.on_exit()
            return

        app = QApplication.instance()
        if app is not None:
            app.quit()
