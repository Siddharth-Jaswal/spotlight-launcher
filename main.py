import sys
import keyboard

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from launcher import Launcher


app = QApplication(sys.argv)

launcher = Launcher()


def hotkey_trigger():
    QTimer.singleShot(0, launcher.open_launcher)


keyboard.add_hotkey("ctrl+alt+space", hotkey_trigger, suppress=True)

sys.exit(app.exec())