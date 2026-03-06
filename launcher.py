import copy
import json
import os
import shlex
import subprocess
import webbrowser
from typing import Any, Callable

from PyQt6.QtCore import QEasingCurve, QEvent, QPoint, QPropertyAnimation, Qt, QVariantAnimation
from PyQt6.QtGui import QColor, QGuiApplication
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFormLayout,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from rapidfuzz import process

from style import STYLE

COMMANDS_FILE = "commands.json"
COMMANDS_FILE_ENV = "SPOTLIGHT_COMMANDS_FILE"
APP_DIR_NAME = "SpotlightLauncher"
WINDOW_WIDTH = 500
WINDOW_BASE_HEIGHT = 60
SUGGESTION_ROW_HEIGHT = 30
MAX_SUGGESTIONS = 5
INPUT_X = 72
INPUT_Y = 8
INPUT_HEIGHT = 44
INPUT_RIGHT_MARGIN = 10
OPEN_CLOSE_ANIMATION_MS = 170
HEIGHT_ANIMATION_MS = 140

CommandEntry = dict[str, Any]


class CommandManagerDialog(QDialog):
    """Dialog used to add, edit, and delete launcher commands."""

    def __init__(
        self,
        entries: list[CommandEntry],
        parent=None,
        on_entries_changed: Callable[[list[CommandEntry]], None] | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Manage Commands")
        self.setModal(True)
        self.resize(620, 420)

        self.entries = [self._normalized_entry(entry) for entry in entries]
        self.editing_index: int | None = None
        self.on_entries_changed = on_entries_changed

        self.list_widget = QListWidget()
        self.name_input = QLineEdit()
        self.target_input = QLineEdit()
        self.type_input = QComboBox()
        self.type_input.addItems(["url", "command"])
        self.aliases_input = QLineEdit()
        self.aliases_input.setPlaceholderText("alias1, alias2")

        form = QFormLayout()
        form.addRow("Name", self.name_input)
        form.addRow("Target", self.target_input)
        form.addRow("Type", self.type_input)
        form.addRow("Aliases", self.aliases_input)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(form)

        action_row = QHBoxLayout()
        self.new_btn = QPushButton("New")
        self.save_btn = QPushButton("Save Entry")
        self.delete_btn = QPushButton("Delete Entry")
        self.done_btn = QPushButton("Done")
        self.cancel_btn = QPushButton("Cancel")

        action_row.addWidget(self.new_btn)
        action_row.addWidget(self.save_btn)
        action_row.addWidget(self.delete_btn)
        action_row.addStretch()
        action_row.addWidget(self.done_btn)
        action_row.addWidget(self.cancel_btn)

        editor_layout.addLayout(action_row)

        content = QHBoxLayout()
        content.addWidget(self.list_widget, 1)
        content.addLayout(editor_layout, 2)

        self.setLayout(content)

        self.list_widget.currentRowChanged.connect(self._load_entry_into_form)
        self.new_btn.clicked.connect(self._new_entry)
        self.save_btn.clicked.connect(self._save_entry)
        self.delete_btn.clicked.connect(self._delete_entry)
        self.done_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        self._refresh_list()

    @staticmethod
    def _normalized_entry(entry: CommandEntry) -> CommandEntry:
        name = str(entry.get("name", "")).strip().lower()
        target = str(entry.get("target", "")).strip()
        cmd_type = str(entry.get("type", "")).strip().lower()
        if cmd_type not in {"url", "command"}:
            cmd_type = "url" if target.startswith("http") else "command"

        aliases = []
        for alias in entry.get("aliases", []):
            value = str(alias).strip().lower()
            if value and value != name and value not in aliases:
                aliases.append(value)

        return {
            "name": name,
            "target": target,
            "type": cmd_type,
            "aliases": aliases,
        }

    def get_entries(self) -> list[CommandEntry]:
        return copy.deepcopy(self.entries)

    def _refresh_list(self, selected_index: int | None = None):
        self.list_widget.clear()
        for entry in self.entries:
            self.list_widget.addItem(entry["name"])

        if not self.entries:
            self._new_entry()
            return

        if selected_index is None:
            selected_index = 0

        selected_index = max(0, min(selected_index, len(self.entries) - 1))
        self.list_widget.setCurrentRow(selected_index)

    def _new_entry(self):
        self.editing_index = None
        self.list_widget.setCurrentRow(-1)
        self.list_widget.setCurrentItem(None)
        self.list_widget.clearSelection()
        self.name_input.clear()
        self.target_input.clear()
        self.type_input.setCurrentText("url")
        self.aliases_input.clear()
        self.name_input.setFocus()

    def _load_entry_into_form(self, row: int):
        if row < 0 or row >= len(self.entries):
            self.editing_index = None
            return

        self.editing_index = row
        entry = self.entries[row]
        self.name_input.setText(entry["name"])
        self.target_input.setText(entry["target"])
        self.type_input.setCurrentText(entry["type"])
        self.aliases_input.setText(", ".join(entry.get("aliases", [])))

    def _build_entry_from_form(self) -> CommandEntry | None:
        name = self.name_input.text().strip().lower()
        target = self.target_input.text().strip()
        cmd_type = self.type_input.currentText().strip().lower()

        aliases = []
        for alias in self.aliases_input.text().split(","):
            value = alias.strip().lower()
            if value and value != name and value not in aliases:
                aliases.append(value)

        if not name:
            QMessageBox.warning(self, "Invalid", "Name is required.")
            return None
        if not target:
            QMessageBox.warning(self, "Invalid", "Target is required.")
            return None

        return {
            "name": name,
            "target": target,
            "type": cmd_type,
            "aliases": aliases,
        }

    def _save_entry(self):
        entry = self._build_entry_from_form()
        if entry is None:
            return

        selected_row = self.editing_index if self.editing_index is not None else -1

        duplicate_index = next(
            (idx for idx, item in enumerate(self.entries) if item["name"] == entry["name"]),
            None,
        )
        if duplicate_index is not None and duplicate_index != selected_row:
            QMessageBox.warning(self, "Duplicate", "Name already exists.")
            return

        if selected_row >= 0:
            self.entries[selected_row] = entry
            new_index = selected_row
        else:
            self.entries.append(entry)
            new_index = len(self.entries) - 1

        self._refresh_list(new_index)
        self._emit_entries_changed()

    def _delete_entry(self):
        selected_row = (
            self.editing_index
            if self.editing_index is not None
            else self.list_widget.currentRow()
        )
        if selected_row < 0 or selected_row >= len(self.entries):
            return

        del self.entries[selected_row]
        if self.entries:
            self._refresh_list(min(selected_row, len(self.entries) - 1))
        else:
            self._refresh_list()
        self._emit_entries_changed()

    def _emit_entries_changed(self):
        if callable(self.on_entries_changed):
            self.on_entries_changed(copy.deepcopy(self.entries))


class Launcher(QWidget):
    """Main spotlight window with command search and execution."""

    def __init__(self, on_exit: Callable[[], None] | None = None):
        super().__init__()
        self.setObjectName("LauncherRoot")
        self.on_exit = on_exit
        self.commands_path = self._resolve_commands_path()
        self._processes: list[subprocess.Popen] = []
        self.base_height = WINDOW_BASE_HEIGHT
        self.max_suggestions = MAX_SUGGESTIONS
        self.suggestion_row_height = SUGGESTION_ROW_HEIGHT

        self.command_entries: list[CommandEntry] = []
        self.commands: dict[str, CommandEntry] = {}
        self.term_to_name: dict[str, str] = {}
        self.command_names: list[str] = []
        self.search_terms: list[str] = []
        self.current_suggestions: list[str] = []

        self._load_commands()

        self.setFixedSize(WINDOW_WIDTH, self.base_height)

        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = int(screen.height() * 0.25)
        self.move(x, y)
        self._rest_pos = QPoint(x, y)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet(STYLE)
        self._apply_depth_effect()
        self._init_animations()

        self.close_btn = QPushButton("", self)
        self.close_btn.setObjectName("trafficClose")
        self.close_btn.setGeometry(14, 24, 12, 12)
        self.close_btn.setToolTip("Exit launcher")
        self.close_btn.clicked.connect(self.exit_app)

        self.min_btn = QPushButton("", self)
        self.min_btn.setObjectName("trafficMin")
        self.min_btn.setGeometry(32, 24, 12, 12)
        self.min_btn.setToolTip("Hide launcher")
        self.min_btn.clicked.connect(self.hide_launcher)

        self.manage_btn = QPushButton("", self)
        self.manage_btn.setObjectName("trafficManage")
        self.manage_btn.setGeometry(50, 24, 12, 12)
        self.manage_btn.setToolTip("Manage commands")
        self.manage_btn.clicked.connect(self.open_manager)

        self.input = QLineEdit(self)
        self.input.setGeometry(
            INPUT_X,
            INPUT_Y,
            WINDOW_WIDTH - INPUT_X - INPUT_RIGHT_MARGIN,
            INPUT_HEIGHT,
        )
        self.input.setPlaceholderText("Search or run command...")
        self.input.returnPressed.connect(self.execute)

        self.list = QListWidget(self)
        self.list.setGeometry(
            0,
            self.base_height,
            WINDOW_WIDTH,
            self.max_suggestions * self.suggestion_row_height,
        )
        self.list.setSpacing(1)
        self.list.hide()

        self.input.textChanged.connect(self.update_suggestions)
        self.list.itemClicked.connect(self.launch_selected)
        self.list.itemActivated.connect(self.launch_selected)
        self.input.installEventFilter(self)

        self.hide()

    def _apply_depth_effect(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(35)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(8, 14, 25, 180))
        self.setGraphicsEffect(shadow)

    def _init_animations(self):
        self._show_fade_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._show_slide_anim = QPropertyAnimation(self, b"pos", self)
        self._hide_fade_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._hide_slide_anim = QPropertyAnimation(self, b"pos", self)
        self._height_anim = QVariantAnimation(self)
        self._hiding_in_progress = False
        self._hide_fade_anim.finished.connect(self._on_hide_animation_finished)

    @staticmethod
    def _resolve_commands_path() -> str:
        env_path = os.environ.get(COMMANDS_FILE_ENV, "").strip()
        if env_path:
            return env_path

        try:
            if os.name == "nt":
                base_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
            else:
                base_dir = os.path.join(os.path.expanduser("~"), ".config")

            app_dir = os.path.join(base_dir, APP_DIR_NAME)
            os.makedirs(app_dir, exist_ok=True)
            return os.path.join(app_dir, COMMANDS_FILE)
        except OSError:
            # Fallback for restricted environments.
            return COMMANDS_FILE

    def _load_commands(self):
        """Load commands from JSON and normalize them for search/indexing."""
        data = {}
        if os.path.exists(self.commands_path):
            try:
                with open(self.commands_path, encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                data = {}

        entries: list[CommandEntry]
        if isinstance(data, dict) and isinstance(data.get("commands"), list):
            entries = data["commands"]
        elif isinstance(data, dict):
            # Backward compatibility for old flat JSON format.
            entries = [
                {
                    "name": str(name).strip().lower(),
                    "target": str(target).strip(),
                    "type": "url" if str(target).strip().startswith("http") else "command",
                    "aliases": [],
                }
                for name, target in data.items()
            ]
        else:
            entries = []

        normalized_entries = []
        seen_names = set()
        for raw in entries:
            entry = CommandManagerDialog._normalized_entry(raw)
            if not entry["name"] or not entry["target"]:
                continue
            if entry["name"] in seen_names:
                continue
            seen_names.add(entry["name"])
            normalized_entries.append(entry)

        self.command_entries = normalized_entries
        self._rebuild_indexes()

    def _save_commands(self):
        parent = os.path.dirname(self.commands_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(self.commands_path, "w", encoding="utf-8") as f:
            json.dump({"commands": self.command_entries}, f, indent=4)

    def _rebuild_indexes(self):
        self.commands = {entry["name"]: entry for entry in self.command_entries}
        self.term_to_name = {}

        for name, entry in self.commands.items():
            self.term_to_name[name] = name
            for alias in entry.get("aliases", []):
                if alias not in self.term_to_name:
                    self.term_to_name[alias] = name

        self.command_names = sorted(self.commands.keys())
        self.search_terms = sorted(self.term_to_name.keys())

    def open_manager(self):
        def _persist_manager_entries(entries: list[CommandEntry]):
            self.command_entries = entries
            self._save_commands()
            self._rebuild_indexes()

        dialog = CommandManagerDialog(
            self.command_entries,
            self,
            on_entries_changed=_persist_manager_entries,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self.command_entries = dialog.get_entries()
        self._save_commands()
        self._rebuild_indexes()
        self._reset_input_state()

    def mousePressEvent(self, event):
        self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = event.globalPosition().toPoint() - self.old_pos
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPosition().toPoint()
        self._rest_pos = self.pos()

    def open_launcher(self):
        if self._hiding_in_progress:
            return
        self._height_anim.stop()
        self._hide_fade_anim.stop()
        self._hide_slide_anim.stop()
        self.move(self._rest_pos + QPoint(0, 10))
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self.activateWindow()
        self.input.setFocus()
        self._animate_show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide_launcher()
            return
        super().keyPressEvent(event)

    def update_suggestions(self, text):
        query = text.strip().lower()
        if not query:
            self.current_suggestions = []
            self.list.clear()
            self._hide_suggestions()
            return

        matches = self._rank_suggestions(query)
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
        resolved_name = self.term_to_name.get(item.text().strip().lower())
        if resolved_name is None:
            return

        self._launch_target(self.commands[resolved_name])
        self.hide_launcher()

    def execute(self):
        raw_cmd = self.input.text().strip().lower()
        resolved_name = self.term_to_name.get(raw_cmd)

        if resolved_name is None and self.current_suggestions:
            current_item = self.list.currentItem()
            suggestion = (
                current_item.text() if current_item else self.current_suggestions[0]
            )
            resolved_name = self.term_to_name.get(suggestion)

        if resolved_name in self.commands:
            self._launch_target(self.commands[resolved_name])

        self.hide_launcher()

    def hide_launcher(self):
        if not self.isVisible() or self._hiding_in_progress:
            return
        self._hiding_in_progress = True
        self._reset_input_state()
        self._animate_hide()

    def eventFilter(self, watched, event):
        if watched is self.input and event.type() == QEvent.Type.KeyPress:
            key = event.key()

            if key == Qt.Key.Key_Tab:
                self._apply_tab_completion()
                return True

            if (
                key in (Qt.Key.Key_Down, Qt.Key.Key_Up)
                and self.list.isVisible()
                and self.list.count() > 0
            ):
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
        prefix_names = [name for name in self.command_names if name.startswith(query)]

        alias_prefix_names = []
        for term in self.search_terms:
            if term.startswith(query):
                resolved = self.term_to_name[term]
                if resolved not in prefix_names and resolved not in alias_prefix_names:
                    alias_prefix_names.append(resolved)

        merged = prefix_names + alias_prefix_names

        if len(merged) < self.max_suggestions:
            contains_names = [
                name
                for name in self.command_names
                if query in name and name not in merged
            ]
            merged.extend(contains_names)

        if len(merged) < self.max_suggestions:
            fuzzy = process.extract(
                query,
                self.search_terms,
                limit=self.max_suggestions * 3,
                score_cutoff=55,
            )
            for term, _, _ in fuzzy:
                resolved = self.term_to_name[term]
                if resolved not in merged:
                    merged.append(resolved)
                if len(merged) >= self.max_suggestions:
                    break

        return merged[: self.max_suggestions]

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
        self._animate_height(self.base_height + list_height, show_list=True)

    def _hide_suggestions(self):
        self.current_suggestions = []
        self._animate_height(self.base_height, show_list=False)

    def _reset_input_state(self):
        """Clear current query/suggestions before hiding the launcher."""
        self.input.clear()
        self._hide_suggestions()

    def _launch_target(self, entry: CommandEntry):
        target = entry["target"]
        entry_type = entry.get("type", "")

        if entry_type == "url" or target.startswith("http"):
            webbrowser.open(target)
            return

        try:
            args = shlex.split(target, posix=(os.name != "nt"))
            if not args:
                raise ValueError("Command target is empty.")
            proc = subprocess.Popen(args)
        except (OSError, ValueError) as first_error:
            try:
                # Windows shell fallback supports command strings like "code .".
                if os.name != "nt":
                    raise first_error
                proc = subprocess.Popen(target, shell=True)
            except OSError as final_error:
                QMessageBox.warning(
                    self,
                    "Launch Failed",
                    f"Could not run command:\n{target}\n\n{final_error}",
                )
                return

        self._processes.append(proc)

    def _animate_show(self):
        self._show_fade_anim.stop()
        self._show_slide_anim.stop()

        self._show_fade_anim.setDuration(OPEN_CLOSE_ANIMATION_MS)
        self._show_fade_anim.setStartValue(self.windowOpacity())
        self._show_fade_anim.setEndValue(1.0)
        self._show_fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._show_slide_anim.setDuration(OPEN_CLOSE_ANIMATION_MS)
        self._show_slide_anim.setStartValue(self.pos())
        self._show_slide_anim.setEndValue(self._rest_pos)
        self._show_slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._show_fade_anim.start()
        self._show_slide_anim.start()

    def _animate_hide(self):
        self._hide_fade_anim.stop()
        self._hide_slide_anim.stop()

        self._hide_fade_anim.setDuration(OPEN_CLOSE_ANIMATION_MS)
        self._hide_fade_anim.setStartValue(self.windowOpacity())
        self._hide_fade_anim.setEndValue(0.0)
        self._hide_fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        self._hide_slide_anim.setDuration(OPEN_CLOSE_ANIMATION_MS)
        self._hide_slide_anim.setStartValue(self.pos())
        self._hide_slide_anim.setEndValue(self._rest_pos + QPoint(0, 8))
        self._hide_slide_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        self._hide_fade_anim.start()
        self._hide_slide_anim.start()

    def _on_hide_animation_finished(self):
        self.hide()
        self.move(self._rest_pos)
        self.setWindowOpacity(1.0)
        self._hiding_in_progress = False

    def _animate_height(self, target_height: int, show_list: bool):
        self._height_anim.stop()
        start_height = self.height()
        target_height = max(self.base_height, target_height)

        if show_list:
            self.list.show()

        self._height_anim = QVariantAnimation(self)
        self._height_anim.setDuration(HEIGHT_ANIMATION_MS)
        self._height_anim.setStartValue(start_height)
        self._height_anim.setEndValue(target_height)
        self._height_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._height_anim.valueChanged.connect(self._apply_height_frame)
        self._height_anim.finished.connect(
            lambda: self._finalize_height(target_height, show_list)
        )
        self._height_anim.start()

    def _apply_height_frame(self, value):
        current_height = int(value)
        list_height = max(0, current_height - self.base_height)
        self.setFixedHeight(current_height)
        self.list.setGeometry(0, self.base_height, WINDOW_WIDTH, list_height)

    def _finalize_height(self, target_height: int, show_list: bool):
        self.setFixedHeight(target_height)
        self.list.setGeometry(
            0,
            self.base_height,
            WINDOW_WIDTH,
            max(0, target_height - self.base_height),
        )
        if not show_list:
            self.list.hide()

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
