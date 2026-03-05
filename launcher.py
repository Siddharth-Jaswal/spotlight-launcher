import json
import webbrowser
import subprocess
import keyboard
import sys
import os

from PyQt6.QtWidgets import QWidget, QLineEdit, QPushButton, QListWidget, QApplication

from PyQt6.QtWidgets import QListWidget
from rapidfuzz import process
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

        # minimize button (hide launcher)
        self.min_btn = QPushButton("—", self)
        self.min_btn.setGeometry(430, 15, 25, 30)
        self.min_btn.clicked.connect(self.hide_launcher)

        # close button (terminate program)
        self.close_btn = QPushButton("✕", self)
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

        # Close button (exit application)
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setGeometry(460, 15, 30, 30)
        self.close_btn.clicked.connect(self.exit_app)

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

    def open_launcher(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()
        self.input.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.input.clear()
            self.hide()
            return

        event.accept()
    
    def update_suggestions(self, text):
        if not text:
            self.list.hide()
            return

        matches = process.extract(
            text,
            self.commands.keys(),
            limit=5
        )

        self.list.clear()

        for match in matches:
            self.list.addItem(match[0])

        self.list.show()

    def launch_selected(self, item):
        cmd = item.text()

        target = self.commands[cmd]

        if target.startswith("http"):
            webbrowser.open(target)
        else:
            subprocess.Popen(target)

        self.input.clear()
        self.list.hide()
        self.hide()

    def execute(self):
        cmd = self.input.text().strip().lower()

        if cmd not in self.commands and self.list.count() > 0:
            cmd = self.list.item(0).text()

        if cmd in self.commands:

            target = self.commands[cmd]

            if target.startswith("http"):
                webbrowser.open(target)
            else:
                subprocess.Popen(target)

        self.input.clear()
        self.list.hide()
        self.hide()

    def exit_app(self):
        QApplication.quit()

    def hide_launcher(self):
        self.input.clear()
        self.list.hide()
        self.hide()


    def exit_app(self):
        os.system(f"taskkill /F /PID {os.getpid()}")


    def keyPressEvent(self, event):

        if event.key() == Qt.Key.Key_Escape:
            self.hide_launcher()
            return

        super().keyPressEvent(event)