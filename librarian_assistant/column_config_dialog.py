# ABOUTME: This file implements a dialog for configuring table column visibility and order.
# ABOUTME: It allows users to show/hide columns and reorder them using up/down buttons.
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                             QListWidgetItem, QPushButton, QDialogButtonBox,
                             QLabel, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal


class ColumnConfigDialog(QDialog):
    """
    Dialog for configuring table column visibility and order.
    Users can show/hide columns with checkboxes and reorder them with up/down buttons.
    """

    # Signal emitted when configuration is accepted
    # Emits (column_names, visible_columns) where both are lists in the new order
    columns_configured = pyqtSignal(list, list)

    def __init__(self, column_names, visible_columns=None, parent=None):
        """
        Initialize the column configuration dialog.

        Args:
            column_names: List of all column names in current order
            visible_columns: List of currently visible column names (if None, all are visible)
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Configure Table Columns")
        self.setModal(True)
        self.resize(400, 500)

        # Store original configuration for cancel/reset
        self.original_column_names = column_names.copy()
        self.original_visible = visible_columns.copy() if visible_columns else column_names.copy()

        # Current configuration
        self.column_names = column_names.copy()
        self.visible_columns = visible_columns.copy() if visible_columns else column_names.copy()

        self._setup_ui()
        self._populate_list()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel("Check columns to show them. Use buttons to reorder.")
        layout.addWidget(instructions)

        # Main content area
        content_layout = QHBoxLayout()

        # Column list
        list_group = QGroupBox("Columns")
        list_layout = QVBoxLayout(list_group)

        self.column_list = QListWidget()
        self.column_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.column_list.itemChanged.connect(self._on_item_changed)
        self.column_list.currentRowChanged.connect(self._on_selection_changed)
        list_layout.addWidget(self.column_list)

        content_layout.addWidget(list_group)

        # Control buttons
        button_layout = QVBoxLayout()
        button_layout.addStretch()

        self.up_button = QPushButton("▲ Move Up")
        self.up_button.clicked.connect(self._move_up)
        self.up_button.setEnabled(False)
        button_layout.addWidget(self.up_button)

        self.down_button = QPushButton("▼ Move Down")
        self.down_button.clicked.connect(self._move_down)
        self.down_button.setEnabled(False)
        button_layout.addWidget(self.down_button)

        button_layout.addSpacing(20)

        self.show_all_button = QPushButton("Show All")
        self.show_all_button.clicked.connect(self._show_all)
        button_layout.addWidget(self.show_all_button)

        self.hide_all_button = QPushButton("Hide All")
        self.hide_all_button.clicked.connect(self._hide_all)
        button_layout.addWidget(self.hide_all_button)

        button_layout.addStretch()
        content_layout.addLayout(button_layout)

        layout.addLayout(content_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Reset
        )
        button_box.accepted.connect(self._accept_configuration)
        button_box.rejected.connect(self.reject)

        # Find and connect reset button
        reset_button = button_box.button(QDialogButtonBox.StandardButton.Reset)
        if reset_button:
            reset_button.clicked.connect(self._reset_to_original)
            reset_button.setToolTip("Reset to configuration when dialog opened")

        # Add a Default button
        default_button = button_box.addButton("Default", QDialogButtonBox.ButtonRole.ResetRole)
        default_button.clicked.connect(self._reset_to_default)
        default_button.setToolTip("Reset to default configuration (all columns visible, original order)")

        layout.addWidget(button_box)

    def _populate_list(self):
        """Populate the list widget with columns."""
        self.column_list.clear()

        for col_name in self.column_names:
            item = QListWidgetItem(col_name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

            # Set check state based on visibility
            if col_name in self.visible_columns:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

            self.column_list.addItem(item)

    def _on_item_changed(self, item):
        """Handle item check state change."""
        col_name = item.text()

        if item.checkState() == Qt.CheckState.Checked:
            if col_name not in self.visible_columns:
                self.visible_columns.append(col_name)
        else:
            if col_name in self.visible_columns:
                self.visible_columns.remove(col_name)

    def _on_selection_changed(self, current_row):
        """Handle selection change to enable/disable move buttons."""
        if current_row < 0:
            self.up_button.setEnabled(False)
            self.down_button.setEnabled(False)
        else:
            self.up_button.setEnabled(current_row > 0)
            self.down_button.setEnabled(current_row < self.column_list.count() - 1)

    def _move_up(self):
        """Move selected item up."""
        current_row = self.column_list.currentRow()
        if current_row > 0:
            # Take item from current position
            item = self.column_list.takeItem(current_row)
            col_name = item.text()

            # Update column order
            self.column_names.remove(col_name)
            self.column_names.insert(current_row - 1, col_name)

            # Reinsert item
            self.column_list.insertItem(current_row - 1, item)
            self.column_list.setCurrentRow(current_row - 1)

    def _move_down(self):
        """Move selected item down."""
        current_row = self.column_list.currentRow()
        if current_row < self.column_list.count() - 1:
            # Take item from current position
            item = self.column_list.takeItem(current_row)
            col_name = item.text()

            # Update column order
            self.column_names.remove(col_name)
            self.column_names.insert(current_row + 1, col_name)

            # Reinsert item
            self.column_list.insertItem(current_row + 1, item)
            self.column_list.setCurrentRow(current_row + 1)

    def _show_all(self):
        """Check all columns."""
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)

    def _hide_all(self):
        """Uncheck all columns."""
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)

    def _reset_to_original(self):
        """Reset to original configuration."""
        self.column_names = self.original_column_names.copy()
        self.visible_columns = self.original_visible.copy()
        self._populate_list()

    def _reset_to_default(self):
        """Reset to default configuration (all visible, original order)."""
        # Default is all columns visible in their original order
        self.column_names = self.original_column_names.copy()
        self.visible_columns = self.original_column_names.copy()
        self._populate_list()

    def _accept_configuration(self):
        """Accept the configuration and emit signal."""
        # Ensure visible columns are in the same order as column_names
        ordered_visible = [col for col in self.column_names if col in self.visible_columns]

        self.columns_configured.emit(self.column_names, ordered_visible)
        self.accept()
