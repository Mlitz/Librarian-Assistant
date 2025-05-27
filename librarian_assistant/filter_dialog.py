# ABOUTME: This file implements the advanced filter dialog for the editions table.
# ABOUTME: It allows users to create multiple filter rules with various operators and combine them with AND/OR logic.
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QLineEdit, QPushButton, QLabel, QGroupBox,
                             QRadioButton, QButtonGroup, QScrollArea, QWidget,
                             QDialogButtonBox, QDateEdit, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QIcon
import logging

logger = logging.getLogger(__name__)


class FilterRule(QWidget):
    """
    A single filter rule widget containing column, operator, and value inputs.
    """
    
    # Signal emitted when remove button is clicked
    remove_requested = pyqtSignal(object)  # Passes self
    
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.columns = columns
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the UI for a single filter rule."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Column selector
        self.column_combo = QComboBox()
        self.column_combo.addItems(self.columns)
        self.column_combo.currentTextChanged.connect(self._on_column_changed)
        layout.addWidget(self.column_combo)
        
        # Operator selector
        self.operator_combo = QComboBox()
        self.operator_combo.setMinimumWidth(150)
        layout.addWidget(self.operator_combo)
        
        # Value input (will be replaced based on operator)
        self.value_widget = QLineEdit()
        self.value_widget.setPlaceholderText("Enter value...")
        layout.addWidget(self.value_widget)
        
        # Remove button
        self.remove_button = QPushButton("✖")
        self.remove_button.setMaximumWidth(30)
        self.remove_button.setToolTip("Remove this filter")
        self.remove_button.clicked.connect(lambda: self.remove_requested.emit(self))
        layout.addWidget(self.remove_button)
        
        # Initialize operators for first column
        self._on_column_changed(self.column_combo.currentText())
    
    def _on_column_changed(self, column_name):
        """Update operators based on selected column type."""
        self.operator_combo.clear()
        
        # Determine column type and appropriate operators
        column_type = self._get_column_type(column_name)
        operators = self._get_operators_for_type(column_type)
        
        self.operator_combo.addItems(operators)
        self.operator_combo.currentTextChanged.connect(self._on_operator_changed)
        self._on_operator_changed(self.operator_combo.currentText())
    
    def _get_column_type(self, column_name):
        """Determine the data type of a column."""
        # Numerical columns
        if column_name in ['score', 'pages', 'Duration']:
            return 'numeric'
        # Date columns
        elif column_name == 'release_date':
            return 'date'
        # Special columns
        elif column_name == 'Cover Image?':
            return 'cover_image'
        elif column_name == 'Reading Format':
            return 'reading_format'
        # Default to text
        else:
            return 'text'
    
    def _get_operators_for_type(self, column_type):
        """Get available operators for a column type."""
        if column_type == 'text':
            return ['Contains', 'Does not contain', 'Equals', 'Does not equal', 
                    'Starts with', 'Ends with', 'Is empty', 'Is not empty']
        elif column_type == 'numeric':
            return ['=', '≠', '>', '>=', '<', '<=', 'Is N/A', 'Is not N/A']
        elif column_type == 'date':
            return ['Is on', 'Is before', 'Is after', 'Is between', 'Is N/A', 'Is not N/A']
        elif column_type == 'cover_image':
            return ['Is "Yes"', 'Is "No"']
        elif column_type == 'reading_format':
            return ['Is', 'Is not']
        else:
            return ['Equals']
    
    def _on_operator_changed(self, operator):
        """Update value widget based on selected operator."""
        # Remove old value widget
        if self.value_widget:
            self.value_widget.setParent(None)
            self.value_widget.deleteLater()
        
        # Create appropriate value widget
        if operator in ['Is empty', 'Is not empty', 'Is N/A', 'Is not N/A', 'Is "Yes"', 'Is "No"']:
            # No value needed
            self.value_widget = QLabel("(no value needed)")
            self.value_widget.setEnabled(False)
        elif operator == 'Is between':
            # Two date inputs
            self.value_widget = QWidget()
            layout = QHBoxLayout(self.value_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            
            self.start_date = QDateEdit()
            self.start_date.setCalendarPopup(True)
            self.start_date.setDate(QDate.currentDate())
            layout.addWidget(self.start_date)
            
            layout.addWidget(QLabel("and"))
            
            self.end_date = QDateEdit()
            self.end_date.setCalendarPopup(True)
            self.end_date.setDate(QDate.currentDate())
            layout.addWidget(self.end_date)
        elif self._get_column_type(self.column_combo.currentText()) == 'date' and operator != 'Is between':
            # Single date input
            self.value_widget = QDateEdit()
            self.value_widget.setCalendarPopup(True)
            self.value_widget.setDate(QDate.currentDate())
        elif self.column_combo.currentText() == 'Reading Format':
            # Dropdown for reading formats
            self.value_widget = QComboBox()
            self.value_widget.addItems(['Physical Book', 'Audiobook', 'E-Book'])
        else:
            # Default text input
            self.value_widget = QLineEdit()
            self.value_widget.setPlaceholderText("Enter value...")
        
        # Add the new value widget
        self.layout().insertWidget(2, self.value_widget)
    
    def get_filter_data(self):
        """Get the filter data as a dictionary."""
        column = self.column_combo.currentText()
        operator = self.operator_combo.currentText()
        
        # Get value based on widget type
        value = None
        if isinstance(self.value_widget, QLineEdit):
            value = self.value_widget.text()
        elif isinstance(self.value_widget, QComboBox):
            value = self.value_widget.currentText()
        elif isinstance(self.value_widget, QDateEdit):
            value = self.value_widget.date().toString('yyyy-MM-dd')
        elif isinstance(self.value_widget, QWidget) and operator == 'Is between':
            # Handle date range
            value = {
                'start': self.start_date.date().toString('yyyy-MM-dd'),
                'end': self.end_date.date().toString('yyyy-MM-dd')
            }
        elif isinstance(self.value_widget, QLabel):
            # No value needed
            value = None
        
        return {
            'column': column,
            'operator': operator,
            'value': value
        }


class FilterDialog(QDialog):
    """
    Advanced filter dialog for the editions table.
    """
    
    # Signal emitted when filters are applied
    filters_applied = pyqtSignal(list, str)  # List of filters and logic mode (AND/OR)
    
    def __init__(self, column_names, parent=None):
        super().__init__(parent)
        self.column_names = column_names
        self.filter_rules = []
        
        self.setWindowTitle("Advanced Filter")
        self.setModal(True)
        self.resize(800, 400)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("Create filter rules to show/hide table rows. Multiple rules can be combined with AND/OR logic.")
        layout.addWidget(instructions)
        
        # Logic selector
        logic_group = QGroupBox("Combine rules with:")
        logic_layout = QHBoxLayout(logic_group)
        
        self.logic_button_group = QButtonGroup()
        self.and_radio = QRadioButton("AND (all rules must match)")
        self.or_radio = QRadioButton("OR (any rule must match)")
        self.and_radio.setChecked(True)
        
        self.logic_button_group.addButton(self.and_radio, 0)
        self.logic_button_group.addButton(self.or_radio, 1)
        
        logic_layout.addWidget(self.and_radio)
        logic_layout.addWidget(self.or_radio)
        logic_layout.addStretch()
        
        layout.addWidget(logic_group)
        
        # Filter rules area
        rules_group = QGroupBox("Filter Rules")
        rules_layout = QVBoxLayout(rules_group)
        
        # Scroll area for rules
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.rules_container = QWidget()
        self.rules_layout = QVBoxLayout(self.rules_container)
        self.rules_layout.setSpacing(5)
        
        scroll_area.setWidget(self.rules_container)
        rules_layout.addWidget(scroll_area)
        
        # Add rule button
        self.add_rule_button = QPushButton("+ Add Filter Rule")
        self.add_rule_button.clicked.connect(self._add_rule)
        rules_layout.addWidget(self.add_rule_button)
        
        layout.addWidget(rules_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.clicked.connect(self._clear_all_rules)
        button_layout.addWidget(self.clear_all_button)
        
        button_layout.addStretch()
        
        button_box = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_filters)
        button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)
        button_layout.addWidget(button_box)
        
        layout.addLayout(button_layout)
        
        # Add an initial rule
        self._add_rule()
    
    def _add_rule(self):
        """Add a new filter rule."""
        rule = FilterRule(self.column_names)
        rule.remove_requested.connect(self._remove_rule)
        
        self.filter_rules.append(rule)
        self.rules_layout.addWidget(rule)
        
        # Update UI state
        self._update_ui_state()
    
    def _remove_rule(self, rule):
        """Remove a filter rule."""
        if rule in self.filter_rules:
            self.filter_rules.remove(rule)
            rule.setParent(None)
            rule.deleteLater()
            
        # Ensure at least one rule exists
        if not self.filter_rules:
            self._add_rule()
        
        # Update UI state
        self._update_ui_state()
    
    def _clear_all_rules(self):
        """Clear all filter rules."""
        # Remove all rules
        for rule in self.filter_rules[:]:
            self._remove_rule(rule)
    
    def _update_ui_state(self):
        """Update UI elements based on current state."""
        # Enable/disable clear all button
        self.clear_all_button.setEnabled(len(self.filter_rules) > 1)
        
        # Enable/disable logic radio buttons
        self.and_radio.setEnabled(len(self.filter_rules) > 1)
        self.or_radio.setEnabled(len(self.filter_rules) > 1)
    
    def _apply_filters(self):
        """Apply the filters and emit signal."""
        # Collect filter data
        filters = []
        for rule in self.filter_rules:
            filter_data = rule.get_filter_data()
            # Only include rules with values (unless operator doesn't need one)
            no_value_operators = ['Is empty', 'Is not empty', 'Is N/A', 'Is not N/A', 'Is "Yes"', 'Is "No"']
            
            if filter_data['operator'] in no_value_operators:
                # These operators don't need values
                filters.append(filter_data)
            elif filter_data['value'] is not None and filter_data['value'] != '':
                # For other operators, only include if value is provided
                filters.append(filter_data)
        
        # Get logic mode
        logic_mode = 'AND' if self.and_radio.isChecked() else 'OR'
        
        # Emit signal
        if filters:
            self.filters_applied.emit(filters, logic_mode)
            self.accept()
        else:
            # No valid filters
            logger.warning("No valid filters to apply")