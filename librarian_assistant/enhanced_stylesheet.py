# ABOUTME: Enhanced stylesheet with modern depth cues and complete widget coverage
# ABOUTME: Provides visual refinements for Phase 8 including shadows, spacing, and consistency

ENHANCED_DARK_THEME = """
/* Enhanced Dark Theme with Depth and Modern Aesthetics */

/* === Global Defaults === */
QWidget {
    background-color: #1a1a1a;
    color: #e0e0e0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 14px;
}

/* === Main Window & Containers === */
QMainWindow {
    background-color: #1a1a1a;
}

QDialog {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 8px;
}

/* === Tab Widget with Depth === */
QTabWidget::pane {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 8px;
    margin-top: -1px;
}

QTabBar::tab {
    background-color: #2a2a2a;
    color: #b0b0b0;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    min-width: 100px;
}

QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: #ffffff;
    border-bottom: 2px solid #6b46c1;
}

QTabBar::tab:hover:!selected {
    background-color: #333333;
    color: #e0e0e0;
}

/* === Group Boxes with Subtle Shadows === */
QGroupBox {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 8px;
    margin-top: 24px;
    padding-top: 20px;
    /* Subtle shadow for depth */
    /* Note: Qt doesn't support box-shadow directly, using gradient as workaround */
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    top: 4px;
    color: #ffffff;
    font-weight: 600;
    font-size: 15px;
}

QGroupBox:!collapsible {
    margin-top: 12px;
}

/* === Enhanced Buttons with Depth === */
QPushButton {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #3a3a3a;
    border-color: #4a4a4a;
}

QPushButton:pressed {
    background-color: #252525;
    border-color: #333333;
}

QPushButton:focus {
    border: 2px solid #6b46c1;
    outline: none;
}

QPushButton#fetchDataButton,
QPushButton#setUpdateTokenButton,
QPushButton#filterButton,
QPushButton#configureColumnsButton {
    background-color: #6b46c1;
    border: none;
    color: #ffffff;
}

QPushButton#fetchDataButton:hover,
QPushButton#setUpdateTokenButton:hover,
QPushButton#filterButton:hover,
QPushButton#configureColumnsButton:hover {
    background-color: #7b56d1;
}

QPushButton#fetchDataButton:pressed,
QPushButton#setUpdateTokenButton:pressed,
QPushButton#filterButton:pressed,
QPushButton#configureColumnsButton:pressed {
    background-color: #5b36b1;
}

/* === Enhanced Input Fields === */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #252525;
    color: #e0e0e0;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #6b46c1;
    selection-color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #6b46c1;
    background-color: #2a2a2a;
}

QLineEdit:read-only, QTextEdit:read-only {
    background-color: #1e1e1e;
    color: #a0a0a0;
}

/* === Enhanced ComboBox (Dropdown) === */
QComboBox {
    background-color: #252525;
    color: #e0e0e0;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #4a4a4a;
    background-color: #2a2a2a;
}

QComboBox:focus {
    border: 2px solid #6b46c1;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #e0e0e0;
    margin-right: 5px;
}

QComboBox QAbstractItemView {
    background-color: #252525;
    border: 1px solid #404040;
    border-radius: 6px;
    selection-background-color: #6b46c1;
    selection-color: #ffffff;
    padding: 4px;
}

/* === Date Edit === */
QDateEdit {
    background-color: #252525;
    color: #e0e0e0;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 20px;
}

QDateEdit:focus {
    border: 2px solid #6b46c1;
}

QDateEdit::drop-down {
    border: none;
    width: 20px;
}

QDateEdit QCalendarWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
}

/* === CheckBox & RadioButton === */
QCheckBox, QRadioButton {
    color: #e0e0e0;
    spacing: 8px;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #404040;
    background-color: #252525;
}

QCheckBox::indicator {
    border-radius: 4px;
}

QRadioButton::indicator {
    border-radius: 9px;
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #6b46c1;
    background-color: #2a2a2a;
}

QCheckBox::indicator:checked {
    background-color: #6b46c1;
    border-color: #6b46c1;
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTQiIGhlaWdodD0iMTQiIHZpZXdCb3g9IjAgMCAxNCAxNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDMuNUw1LjUgMTBMMiA2LjUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPg==);
}

QRadioButton::indicator:checked {
    background-color: #6b46c1;
    border-color: #6b46c1;
}

QRadioButton::indicator:checked::after {
    content: "";
    width: 8px;
    height: 8px;
    border-radius: 4px;
    background-color: #ffffff;
    position: absolute;
    left: 5px;
    top: 5px;
}

/* === Enhanced Tables === */
QTableWidget {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 6px;
    gridline-color: #2a2a2a;
    selection-background-color: #6b46c1;
    selection-color: #ffffff;
}

QTableWidget::item {
    padding: 6px 8px;
    border: none;
}

QTableWidget::item:selected {
    background-color: #6b46c1;
    color: #ffffff;
}

QTableWidget::item:hover {
    background-color: #2a2a2a;
}

QHeaderView::section {
    background-color: #252525;
    color: #ffffff;
    padding: 8px 12px;
    border: none;
    border-bottom: 2px solid #333333;
    font-weight: 600;
}

QHeaderView::section:hover {
    background-color: #2a2a2a;
}

QTableCornerButton::section {
    background-color: #252525;
    border: none;
    border-bottom: 2px solid #333333;
    border-right: 2px solid #333333;
}

/* === Enhanced Scroll Bars === */
QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 12px;
    border: none;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background-color: #404040;
    border-radius: 5px;
    min-height: 30px;
    margin: 1px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4a4a4a;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 12px;
    border: none;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background-color: #404040;
    border-radius: 5px;
    min-width: 30px;
    margin: 1px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #4a4a4a;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* === Status Bar === */
QStatusBar {
    background-color: #1e1e1e;
    color: #b0b0b0;
    border-top: 1px solid #333333;
    padding: 4px 12px;
}

/* === Labels === */
QLabel {
    color: #e0e0e0;
    background-color: transparent;
}

QLabel[accessibleName="link"] {
    color: #8ab4f8;
    text-decoration: underline;
}

QLabel[accessibleName="link"]:hover {
    color: #aac7ff;
}

/* === Tooltips === */
QToolTip {
    background-color: #2a2a2a;
    color: #ffffff;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
}

/* === Message Box === */
QMessageBox {
    background-color: #1e1e1e;
    color: #e0e0e0;
}

QMessageBox QPushButton {
    min-width: 80px;
    margin: 4px;
}

/* === Dialog Button Box === */
QDialogButtonBox {
    dialogbuttonbox-buttons-have-icons: 0;
    spacing: 8px;
    padding: 8px;
}

/* === Splitter === */
QSplitter::handle {
    background-color: #333333;
}

QSplitter::handle:hover {
    background-color: #404040;
}

/* === Progress Bar === */
QProgressBar {
    background-color: #252525;
    border: 1px solid #404040;
    border-radius: 4px;
    text-align: center;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #6b46c1;
    border-radius: 3px;
}

/* === Spin Box === */
QSpinBox, QDoubleSpinBox {
    background-color: #252525;
    color: #e0e0e0;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 20px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #6b46c1;
}

/* === Slider === */
QSlider::groove:horizontal {
    background-color: #252525;
    height: 6px;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #6b46c1;
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -5px 0;
}

QSlider::handle:horizontal:hover {
    background-color: #7b56d1;
}

/* === List Widget === */
QListWidget {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 4px;
}

QListWidget::item {
    padding: 6px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #6b46c1;
    color: #ffffff;
}

QListWidget::item:hover {
    background-color: #2a2a2a;
}

/* === Tree Widget === */
QTreeWidget {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 6px;
    alternate-background-color: #222222;
}

QTreeWidget::item {
    padding: 4px;
}

QTreeWidget::item:selected {
    background-color: #6b46c1;
    color: #ffffff;
}

QTreeWidget::item:hover {
    background-color: #2a2a2a;
}

QTreeWidget::branch {
    background-color: #1e1e1e;
}

/* === Menu === */
QMenu {
    background-color: #252525;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #6b46c1;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #404040;
    margin: 4px 8px;
}

/* === Custom Spacing Classes === */
.spacing-tight {
    margin: 4px;
    padding: 4px;
}

.spacing-normal {
    margin: 8px;
    padding: 8px;
}

.spacing-relaxed {
    margin: 12px;
    padding: 12px;
}

.spacing-loose {
    margin: 16px;
    padding: 16px;
}

/* === Depth Classes for Elevation === */
.elevation-1 {
    background-color: #1e1e1e;
}

.elevation-2 {
    background-color: #252525;
}

.elevation-3 {
    background-color: #2a2a2a;
}

.elevation-4 {
    background-color: #333333;
}

/* === Special UI Elements === */
/* Book Mappings Card */
.book-mapping-card {
    background-color: #242424;
    border: 1px solid #3d3d3d;
    border-radius: 8px;
    margin: 10px;
    padding: 15px;
}

/* Instruction/Help Text */
.help-text {
    color: #888888;
    font-style: italic;
}

/* Error/Warning States */
.error {
    color: #ff6b6b;
}

.warning {
    color: #ffd93d;
}

.success {
    color: #6bcf7f;
}

/* Link Styling */
.clickable-link {
    color: #8ab4f8;
    text-decoration: underline;
}

.clickable-link:hover {
    color: #aac7ff;
    cursor: pointer;
}
"""

# Spacing constants for consistent layout
SPACING = {
    'xs': 4,
    'sm': 8,
    'md': 12,
    'lg': 16,
    'xl': 24,
    'xxl': 32
}

# Elevation shadow styles (for custom painting if needed)
ELEVATION_SHADOWS = {
    1: "0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24)",
    2: "0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23)",
    3: "0 10px 20px rgba(0, 0, 0, 0.19), 0 6px 6px rgba(0, 0, 0, 0.23)",
    4: "0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22)",
    5: "0 19px 38px rgba(0, 0, 0, 0.30), 0 15px 12px rgba(0, 0, 0, 0.22)"
}
