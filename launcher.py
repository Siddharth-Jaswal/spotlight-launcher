import json
import os
import subprocess
import webbrowser
from typing import Callable

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication, QListWidget, QLineEdit, QPushButton, QWidget
from rapidfuzz import process

from style import STYLE


class Launcher(QWidget):
    def __init__(self, on_exit: Callable[[], None] | None = None):
        super().__init__()
        self.on_exit = on_exit
        self._processes: list[subprocess.Popen] = []
        self.base_height = 60
        self.max_suggestions = 5
        self.suggestion_row_height = 30

        with open("commands.json", encoding="utf-8") as f:
            self.commands = json.load(f)
        self.command_names = sorted(self.commands.keys())
        self.current_suggestions: list[str] = []

        self.setFixedSize(500, self.base_height)

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
        self.list.setGeometry(
            0,
            self.base_height,
            500,
            self.max_suggestions * self.suggestion_row_height,
        )
        self.list.hide()

        self.input.textChanged.connect(self.update_suggestions)
        self.list.itemClicked.connect(self.launch_selected)
        self.list.itemActivated.connect(self.launch_selected)
        self.input.installEventFilter(self)

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
        query = text.strip()
        if not query:
            self.current_suggestions = []
            self.list.clear()
            self._hide_suggestions()
            return

        matches = self._rank_suggestions(query.lower())
        self.current_suggestions = matches
        self.list.clear()

        for match in matches:
            self.list.addItem(match)

        if self.list.count() == 0:
            self._hide_suggestions()
            return

        self.list.setCurrentRow(0)
        self._show_suggestions()

    def launch_selected(self, item):
        cmd = item.text()
        target = self.commands[cmd]
        self._launch_target(target)

        self.input.clear()
        self._hide_suggestions()
        self.hide()

    def execute(self):
        cmd = self.input.text().strip().lower()

        if cmd not in self.commands and self.current_suggestions:
            current_item = self.list.currentItem()
            cmd = current_item.text() if current_item else self.current_suggestions[0]

        if cmd in self.commands:
            target = self.commands[cmd]
            self._launch_target(target)

        self.input.clear()
        self._hide_suggestions()
        self.hide()

    def hide_launcher(self):
        self.input.clear()
        self._hide_suggestions()
        self.hide()

    def eventFilter(self, watched, event):
        if watched is self.input and event.type() == QEvent.Type.KeyPress:
            key = event.key()

            if key == Qt.Key.Key_Tab:
                self._apply_tab_completion()
                return True

            if key in (Qt.Key.Key_Down, Qt.Key.Key_Up) and self.list.isVisible() and self.list.count() > 0:
                step = 1 if key == Qt.Key.Key_Down else -1
                row = max(0, self.list.currentRow())
                next_row = (row + step) % self.list.count()
                self.list.setCurrentRow(next_row)
                return True

        return super().eventFilter(watched, event)

    def _apply_tab_completion(self):
        query = self.input.text().strip().lower()
        if query and not self.current_suggestions:
            self.update_suggestions(query)

        if not self.current_suggestions:
            return

        completion = self._common_prefix(self.current_suggestions)
        if len(completion) <= len(query):
            completion = self.current_suggestions[0]

        self.input.setText(completion)
        self.input.setSelection(len(query), len(completion) - len(query))
        self.update_suggestions(completion)

    def _rank_suggestions(self, query: str) -> list[str]:
        prefix = [name for name in self.command_names if name.startswith(query)]
        if len(prefix) >= self.max_suggestions:
            return prefix[: self.max_suggestions]

        contains = [
            name for name in self.command_names if query in name and not name.startswith(query)
        ]
        merged = prefix + contains
        if len(merged) >= self.max_suggestions:
            return merged[: self.max_suggestions]

        fuzzy = process.extract(
            query,
            self.command_names,
            limit=self.max_suggestions * 3,
            score_cutoff=55,
        )
        for name, _, _ in fuzzy:
            if name not in merged:
                merged.append(name)
            if len(merged) >= self.max_suggestions:
                break

        return merged

    @staticmethod
    def _common_prefix(words: list[str]) -> str:
        if not words:
            return ""

        prefix = words[0]
        for word in words[1:]:
            while not word.startswith(prefix) and prefix:
                prefix = prefix[:-1]
        return prefix

    def _show_suggestions(self):
        item_count = min(self.list.count(), self.max_suggestions)
        list_height = item_count * self.suggestion_row_height
        self.list.setGeometry(0, self.base_height, 500, list_height)
        self.setFixedHeight(self.base_height + list_height)
        self.list.show()

    def _hide_suggestions(self):
        self.current_suggestions = []
        self.list.hide()
        self.setFixedHeight(self.base_height)

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
