# ABOUTME: This file contains unit tests for the FilterDialog and FilterRule classes.
# ABOUTME: It tests filter creation, operator selection, value input, and filter application.
import unittest
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication, QLineEdit, QComboBox, QDateEdit, QLabel, QWidget
from PyQt5.QtCore import Qt, QDate
import sys

# Import the classes to test
from librarian_assistant.filter_dialog import FilterDialog, FilterRule


class TestFilterRule(unittest.TestCase):
    """Test cases for FilterRule widget."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_columns = ['id', 'title', 'score', 'pages', 'release_date', 
                            'Cover Image?', 'Reading Format', 'author']
        
    def test_filter_rule_initialization(self):
        """Test FilterRule initializes correctly."""
        rule = FilterRule(self.test_columns)
        
        # Check widgets exist
        self.assertIsNotNone(rule.column_combo)
        self.assertIsNotNone(rule.operator_combo)
        self.assertIsNotNone(rule.value_widget)
        self.assertIsNotNone(rule.remove_button)
        
        # Check columns populated
        self.assertEqual(rule.column_combo.count(), len(self.test_columns))
        
        # Check operators populated (should be text operators for 'id')
        self.assertGreater(rule.operator_combo.count(), 0)
    
    def test_column_type_detection(self):
        """Test correct column type detection."""
        rule = FilterRule(self.test_columns)
        
        # Test various column types
        self.assertEqual(rule._get_column_type('score'), 'numeric')
        self.assertEqual(rule._get_column_type('pages'), 'numeric')
        self.assertEqual(rule._get_column_type('Duration'), 'numeric')
        self.assertEqual(rule._get_column_type('release_date'), 'date')
        self.assertEqual(rule._get_column_type('Cover Image?'), 'cover_image')
        self.assertEqual(rule._get_column_type('Reading Format'), 'reading_format')
        self.assertEqual(rule._get_column_type('title'), 'text')
        self.assertEqual(rule._get_column_type('author'), 'text')
    
    def test_operators_for_text_columns(self):
        """Test operators for text columns."""
        rule = FilterRule(self.test_columns)
        rule.column_combo.setCurrentText('title')
        
        operators = [rule.operator_combo.itemText(i) for i in range(rule.operator_combo.count())]
        expected_operators = ['Contains', 'Does not contain', 'Equals', 'Does not equal', 
                            'Starts with', 'Ends with', 'Is empty', 'Is not empty']
        self.assertEqual(operators, expected_operators)
    
    def test_operators_for_numeric_columns(self):
        """Test operators for numeric columns."""
        rule = FilterRule(self.test_columns)
        rule.column_combo.setCurrentText('score')
        
        operators = [rule.operator_combo.itemText(i) for i in range(rule.operator_combo.count())]
        expected_operators = ['=', '≠', '>', '>=', '<', '<=', 'Is N/A', 'Is not N/A']
        self.assertEqual(operators, expected_operators)
    
    def test_operators_for_date_columns(self):
        """Test operators for date columns."""
        rule = FilterRule(self.test_columns)
        rule.column_combo.setCurrentText('release_date')
        
        operators = [rule.operator_combo.itemText(i) for i in range(rule.operator_combo.count())]
        expected_operators = ['Is on', 'Is before', 'Is after', 'Is between', 'Is N/A', 'Is not N/A']
        self.assertEqual(operators, expected_operators)
    
    def test_value_widget_for_text_input(self):
        """Test value widget is QLineEdit for text operators."""
        rule = FilterRule(self.test_columns)
        rule.column_combo.setCurrentText('title')
        rule.operator_combo.setCurrentText('Contains')
        
        self.assertIsInstance(rule.value_widget, QLineEdit)
    
    def test_value_widget_for_no_value_operators(self):
        """Test value widget for operators that don't need values."""
        rule = FilterRule(self.test_columns)
        
        # Test "Is empty"
        rule.column_combo.setCurrentText('title')
        rule.operator_combo.setCurrentText('Is empty')
        self.assertIsInstance(rule.value_widget, QLabel)
        self.assertFalse(rule.value_widget.isEnabled())
        
        # Test "Is N/A"
        rule.column_combo.setCurrentText('score')
        rule.operator_combo.setCurrentText('Is N/A')
        self.assertIsInstance(rule.value_widget, QLabel)
        self.assertFalse(rule.value_widget.isEnabled())
    
    def test_value_widget_for_date_input(self):
        """Test value widget is QDateEdit for date operators."""
        rule = FilterRule(self.test_columns)
        rule.column_combo.setCurrentText('release_date')
        rule.operator_combo.setCurrentText('Is on')
        
        self.assertIsInstance(rule.value_widget, QDateEdit)
    
    def test_value_widget_for_date_range(self):
        """Test value widget for 'Is between' date operator."""
        rule = FilterRule(self.test_columns)
        rule.column_combo.setCurrentText('release_date')
        rule.operator_combo.setCurrentText('Is between')
        
        self.assertIsInstance(rule.value_widget, QWidget)
        # Check it has start_date and end_date attributes
        self.assertTrue(hasattr(rule, 'start_date'))
        self.assertTrue(hasattr(rule, 'end_date'))
        self.assertIsInstance(rule.start_date, QDateEdit)
        self.assertIsInstance(rule.end_date, QDateEdit)
    
    def test_value_widget_for_reading_format(self):
        """Test value widget is QComboBox for Reading Format."""
        rule = FilterRule(self.test_columns)
        rule.column_combo.setCurrentText('Reading Format')
        rule.operator_combo.setCurrentText('Is')
        
        self.assertIsInstance(rule.value_widget, QComboBox)
        self.assertEqual(rule.value_widget.count(), 3)  # Physical Book, Audiobook, E-Book
    
    def test_get_filter_data_text(self):
        """Test getting filter data for text filter."""
        rule = FilterRule(self.test_columns)
        rule.column_combo.setCurrentText('title')
        rule.operator_combo.setCurrentText('Contains')
        rule.value_widget.setText('Harry Potter')
        
        data = rule.get_filter_data()
        self.assertEqual(data['column'], 'title')
        self.assertEqual(data['operator'], 'Contains')
        self.assertEqual(data['value'], 'Harry Potter')
    
    def test_get_filter_data_numeric(self):
        """Test getting filter data for numeric filter."""
        rule = FilterRule(self.test_columns)
        rule.column_combo.setCurrentText('score')
        rule.operator_combo.setCurrentText('>')
        rule.value_widget.setText('4.5')
        
        data = rule.get_filter_data()
        self.assertEqual(data['column'], 'score')
        self.assertEqual(data['operator'], '>')
        self.assertEqual(data['value'], '4.5')
    
    def test_get_filter_data_date(self):
        """Test getting filter data for date filter."""
        rule = FilterRule(self.test_columns)
        rule.column_combo.setCurrentText('release_date')
        rule.operator_combo.setCurrentText('Is after')
        
        test_date = QDate(2023, 1, 1)
        rule.value_widget.setDate(test_date)
        
        data = rule.get_filter_data()
        self.assertEqual(data['column'], 'release_date')
        self.assertEqual(data['operator'], 'Is after')
        self.assertEqual(data['value'], '2023-01-01')
    
    def test_get_filter_data_date_range(self):
        """Test getting filter data for date range."""
        rule = FilterRule(self.test_columns)
        rule.column_combo.setCurrentText('release_date')
        rule.operator_combo.setCurrentText('Is between')
        
        start_date = QDate(2023, 1, 1)
        end_date = QDate(2023, 12, 31)
        rule.start_date.setDate(start_date)
        rule.end_date.setDate(end_date)
        
        data = rule.get_filter_data()
        self.assertEqual(data['column'], 'release_date')
        self.assertEqual(data['operator'], 'Is between')
        self.assertEqual(data['value']['start'], '2023-01-01')
        self.assertEqual(data['value']['end'], '2023-12-31')
    
    def test_remove_signal(self):
        """Test remove button emits signal."""
        rule = FilterRule(self.test_columns)
        
        # Connect signal spy
        signal_spy = Mock()
        rule.remove_requested.connect(signal_spy)
        
        # Click remove button
        rule.remove_button.click()
        
        # Check signal emitted with self
        signal_spy.assert_called_once_with(rule)


class TestFilterDialog(unittest.TestCase):
    """Test cases for FilterDialog."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_columns = ['id', 'title', 'score', 'pages', 'author']
        
    def test_dialog_initialization(self):
        """Test FilterDialog initializes correctly."""
        dialog = FilterDialog(self.test_columns)
        
        # Check window properties
        self.assertEqual(dialog.windowTitle(), "Advanced Filter")
        self.assertTrue(dialog.isModal())
        
        # Check initial rule exists
        self.assertEqual(len(dialog.filter_rules), 1)
        
        # Check logic radio buttons
        self.assertTrue(dialog.and_radio.isChecked())
        self.assertFalse(dialog.or_radio.isChecked())
        
        # Check buttons exist
        self.assertIsNotNone(dialog.add_rule_button)
        self.assertIsNotNone(dialog.clear_all_button)
    
    def test_add_rule(self):
        """Test adding filter rules."""
        dialog = FilterDialog(self.test_columns)
        
        # Should start with 1 rule
        self.assertEqual(len(dialog.filter_rules), 1)
        
        # Add another rule
        dialog._add_rule()
        self.assertEqual(len(dialog.filter_rules), 2)
        
        # Add one more
        dialog._add_rule()
        self.assertEqual(len(dialog.filter_rules), 3)
    
    def test_remove_rule(self):
        """Test removing filter rules."""
        dialog = FilterDialog(self.test_columns)
        
        # Add extra rules
        dialog._add_rule()
        dialog._add_rule()
        self.assertEqual(len(dialog.filter_rules), 3)
        
        # Remove a rule
        rule_to_remove = dialog.filter_rules[1]
        dialog._remove_rule(rule_to_remove)
        self.assertEqual(len(dialog.filter_rules), 2)
        self.assertNotIn(rule_to_remove, dialog.filter_rules)
    
    def test_minimum_one_rule(self):
        """Test that at least one rule is always present."""
        dialog = FilterDialog(self.test_columns)
        
        # Try to remove the only rule
        rule = dialog.filter_rules[0]
        dialog._remove_rule(rule)
        
        # Should create a new rule automatically
        self.assertEqual(len(dialog.filter_rules), 1)
        self.assertNotEqual(dialog.filter_rules[0], rule)  # New rule created
    
    def test_clear_all_rules(self):
        """Test clearing all rules."""
        dialog = FilterDialog(self.test_columns)
        
        # Add multiple rules
        dialog._add_rule()
        dialog._add_rule()
        dialog._add_rule()
        self.assertEqual(len(dialog.filter_rules), 4)
        
        # Clear all
        dialog._clear_all_rules()
        
        # Should have one rule (minimum)
        self.assertEqual(len(dialog.filter_rules), 1)
    
    def test_ui_state_updates(self):
        """Test UI state updates based on rule count."""
        dialog = FilterDialog(self.test_columns)
        
        # With one rule, logic buttons and clear all should be disabled
        self.assertFalse(dialog.and_radio.isEnabled())
        self.assertFalse(dialog.or_radio.isEnabled())
        self.assertFalse(dialog.clear_all_button.isEnabled())
        
        # Add a rule
        dialog._add_rule()
        
        # With multiple rules, they should be enabled
        self.assertTrue(dialog.and_radio.isEnabled())
        self.assertTrue(dialog.or_radio.isEnabled())
        self.assertTrue(dialog.clear_all_button.isEnabled())
    
    def test_apply_filters_signal(self):
        """Test applying filters emits correct signal."""
        dialog = FilterDialog(self.test_columns)
        
        # Set up signal spy
        signal_spy = Mock()
        dialog.filters_applied.connect(signal_spy)
        
        # Set up a filter
        rule = dialog.filter_rules[0]
        rule.column_combo.setCurrentText('title')
        rule.operator_combo.setCurrentText('Contains')
        rule.value_widget.setText('Test')
        
        # Apply filters
        dialog._apply_filters()
        
        # Check signal emitted
        signal_spy.assert_called_once()
        filters, logic_mode = signal_spy.call_args[0]
        
        self.assertEqual(len(filters), 1)
        self.assertEqual(filters[0]['column'], 'title')
        self.assertEqual(filters[0]['operator'], 'Contains')
        self.assertEqual(filters[0]['value'], 'Test')
        self.assertEqual(logic_mode, 'AND')
    
    def test_apply_filters_with_or_logic(self):
        """Test applying filters with OR logic."""
        dialog = FilterDialog(self.test_columns)
        
        # Add another rule
        dialog._add_rule()
        
        # Select OR
        dialog.or_radio.setChecked(True)
        
        # Set up signal spy
        signal_spy = Mock()
        dialog.filters_applied.connect(signal_spy)
        
        # Set up filters
        dialog.filter_rules[0].column_combo.setCurrentText('title')
        dialog.filter_rules[0].operator_combo.setCurrentText('Contains')
        dialog.filter_rules[0].value_widget.setText('Harry')
        
        dialog.filter_rules[1].column_combo.setCurrentText('score')
        dialog.filter_rules[1].operator_combo.setCurrentText('>')
        dialog.filter_rules[1].value_widget.setText('4')
        
        # Apply filters
        dialog._apply_filters()
        
        # Check signal emitted
        signal_spy.assert_called_once()
        filters, logic_mode = signal_spy.call_args[0]
        
        self.assertEqual(len(filters), 2)
        self.assertEqual(logic_mode, 'OR')
    
    def test_empty_filters_not_applied(self):
        """Test that empty filters are not included."""
        dialog = FilterDialog(self.test_columns)
        
        # Add rules but don't set values
        dialog._add_rule()
        dialog._add_rule()
        
        # Set up signal spy
        signal_spy = Mock()
        dialog.filters_applied.connect(signal_spy)
        
        # Set only one valid filter
        dialog.filter_rules[0].column_combo.setCurrentText('title')
        dialog.filter_rules[0].operator_combo.setCurrentText('Contains')
        dialog.filter_rules[0].value_widget.setText('Test')
        
        # Leave other rules empty
        
        # Apply filters
        dialog._apply_filters()
        
        # Check only valid filter included
        signal_spy.assert_called_once()
        filters, _ = signal_spy.call_args[0]
        self.assertEqual(len(filters), 1)
    
    def test_no_value_operators_included(self):
        """Test operators that don't need values are included."""
        dialog = FilterDialog(self.test_columns)
        
        # Set up signal spy
        signal_spy = Mock()
        dialog.filters_applied.connect(signal_spy)
        
        # Set up filter with no-value operator
        rule = dialog.filter_rules[0]
        rule.column_combo.setCurrentText('title')
        rule.operator_combo.setCurrentText('Is empty')
        
        # Apply filters
        dialog._apply_filters()
        
        # Check filter included even without value
        signal_spy.assert_called_once()
        filters, _ = signal_spy.call_args[0]
        self.assertEqual(len(filters), 1)
        self.assertEqual(filters[0]['operator'], 'Is empty')
        self.assertIsNone(filters[0]['value'])


if __name__ == '__main__':
    unittest.main()