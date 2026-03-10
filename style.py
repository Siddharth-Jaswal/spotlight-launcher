STYLE = """
QWidget {
    font-family: "SF Pro Text", "Segoe UI Variable", "Segoe UI";
    color: #1d1d1f;
}

QWidget#LauncherRoot {
    background-color: rgba(246, 246, 248, 0.94);
    border: 1px solid rgba(176, 176, 182, 0.75);
    border-radius: 16px;
}

QLineEdit {
    background-color: rgba(255, 255, 255, 0.78);
    border: 1px solid rgba(170, 170, 178, 0.85);
    border-radius: 12px;
    color: #1f1f22;
    font-size: 18px;
    font-weight: 600;
    padding: 0 14px;
    selection-background-color: #0a84ff;
    selection-color: #ffffff;
}

QLineEdit:focus {
    border: 2px solid #0a84ff;
    padding: 0 13px;
    background-color: rgba(255, 255, 255, 0.95);
}

QListWidget#SuggestionList {
    background-color: rgba(255, 255, 255, 0.96);
    border: 1px solid rgba(184, 184, 191, 0.9);
    border-radius: 14px;
    color: #212124;
    font-size: 14px;
    outline: none;
    padding: 4px 6px 6px 6px;
}

QListWidget#SuggestionList::item {
    border-radius: 9px;
    color: #212124;
    padding: 9px 12px;
    margin: 1px 0;
}

QListWidget#SuggestionList::item:hover {
    background-color: #f1f2f5;
}

QListWidget#SuggestionList::item:selected,
QListWidget#SuggestionList::item:selected:active,
QListWidget#SuggestionList::item:selected:!active {
    background-color: #0a84ff;
    color: #ffffff;
    border: none;
}

QListWidget {
    background-color: #ffffff;
    border: 1px solid #d8d8de;
    border-radius: 10px;
    color: #212124;
    font-size: 14px;
    outline: none;
    padding: 4px;
}

QListWidget::item {
    border-radius: 8px;
    padding: 6px 8px;
    margin: 1px 0;
}

QListWidget::item:hover {
    background-color: #f1f2f5;
}

QListWidget::item:selected {
    background-color: #0a84ff;
    color: #ffffff;
}

QPushButton {
    background-color: #f2f2f7;
    border: 1px solid #d6d6de;
    border-radius: 10px;
    color: #1d1d1f;
    font-size: 13px;
    font-weight: 600;
    min-height: 30px;
    padding: 0 12px;
}

QPushButton:hover {
    background-color: #e8e8ef;
}

QPushButton:pressed {
    background-color: #dfe0e9;
}

QPushButton#trafficClose,
QPushButton#trafficMin,
QPushButton#trafficManage {
    min-height: 12px;
    max-height: 12px;
    min-width: 12px;
    max-width: 12px;
    border-radius: 6px;
    border: 1px solid rgba(0, 0, 0, 0.22);
    padding: 0;
}

QPushButton#trafficClose {
    background-color: #ff5f57;
}

QPushButton#trafficMin {
    background-color: #febc2e;
}

QPushButton#trafficManage {
    background-color: #28c840;
}

QPushButton#trafficClose:hover {
    background-color: #ff4d45;
}

QPushButton#trafficMin:hover {
    background-color: #f5ae17;
}

QPushButton#trafficManage:hover {
    background-color: #1fba36;
}

QDialog {
    background-color: #f5f5f7;
}

QComboBox {
    border: 1px solid #cacad1;
    border-radius: 8px;
    background-color: #ffffff;
    color: #1d1d1f;
    min-height: 30px;
    padding: 0 8px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #1d1d1f;
    border: 1px solid #cacad1;
    selection-background-color: #0a84ff;
    selection-color: #ffffff;
}

QLabel {
    color: #3a3a40;
    font-size: 13px;
    font-weight: 500;
}
"""
