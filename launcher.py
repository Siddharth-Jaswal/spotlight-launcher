import sys
import json
import webbrowser
import subprocess

from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit
from PyQt6.QtCore import Qt


class Launcher(QWidget):

    def __init__(self):
        super().__init__()

        with open("commands.json") as f:
            self.commands = json.load(f)

        self.setWindowTitle("Spotlight Launcher")
        self.setFixedSize(500, 60)

        self.input = QLineEdit(self)
        self.input.setGeometry(0, 0, 500, 60)
        self.input.setPlaceholderText("Type command...")
        self.input.returnPressed.connect(self.execute)

    def execute(self):

        cmd = self.input.text().strip().lower()

        if cmd in self.commands:

            target = self.commands[cmd]

            if target.startswith("http"):
                webbrowser.open(target)
            else:
                subprocess.Popen(target)

        self.input.clear()


app = QApplication(sys.argv)

window = Launcher()
window.show()

sys.exit(app.exec())