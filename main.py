import ctypes
import ctypes.wintypes as wintypes
import os
import subprocess
import sys
import threading

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from pynput import keyboard

from launcher import Launcher

HOTKEY_MESSAGE_ID = 0x0312
WM_QUIT = 0x0012
HOTKEY_ID = 1
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
VK_SPACE = 0x20
DETACHED_CHILD_ENV = "SPOTLIGHT_SID_CHILD"


class UiBridge(QObject):
    """Bridge object so worker threads can request UI actions safely."""

    show_launcher = pyqtSignal()


def _windows_background_python_executable() -> str:
    """Use pythonw when available so launching doesn't create a console window."""
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    return pythonw if os.path.exists(pythonw) else sys.executable


def run_cli():
    """CLI entrypoint used by installed command scripts."""
    if os.name != "nt" or os.environ.get(DETACHED_CHILD_ENV) == "1":
        return run()

    env = os.environ.copy()
    env[DETACHED_CHILD_ENV] = "1"

    subprocess.Popen(
        [_windows_background_python_executable(), "-m", "main"],
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )
    return 0


def run():
    """Start the Qt app and global hotkey listener."""
    app = QApplication(sys.argv)
    shutdown_started = threading.Event()
    hotkey_thread_id = None
    ui_bridge = UiBridge()

    def hotkey_trigger():
        if shutdown_started.is_set():
            return
        ui_bridge.show_launcher.emit()

    def start_win_hotkey_listener():
        nonlocal hotkey_thread_id

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        hotkey_thread_id = kernel32.GetCurrentThreadId()

        if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_ALT, VK_SPACE):
            return

        msg = wintypes.MSG()
        try:
            while not shutdown_started.is_set():
                result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if result <= 0:
                    break

                if msg.message == HOTKEY_MESSAGE_ID and msg.wParam == HOTKEY_ID:
                    hotkey_trigger()

                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)

    def start_fallback_hotkey_listener():
        with keyboard.GlobalHotKeys({"<ctrl>+<alt>+<space>": hotkey_trigger}) as listener:
            listener.join()

    launcher = Launcher()

    def shutdown():
        if shutdown_started.is_set():
            return

        shutdown_started.set()
        launcher.shutdown_processes()

        if os.name == "nt" and hotkey_thread_id is not None:
            ctypes.windll.user32.PostThreadMessageW(hotkey_thread_id, WM_QUIT, 0, 0)

        if listener_thread.is_alive():
            listener_thread.join(timeout=2)

        app.quit()

    launcher.on_exit = shutdown
    ui_bridge.show_launcher.connect(launcher.open_launcher)
    app.aboutToQuit.connect(shutdown)

    listener_target = (
        start_win_hotkey_listener if os.name == "nt" else start_fallback_hotkey_listener
    )
    listener_thread = threading.Thread(target=listener_target, daemon=True)
    listener_thread.start()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run_cli())
