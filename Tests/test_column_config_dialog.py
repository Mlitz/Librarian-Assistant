# ABOUTME: This file contains unit tests for the ColumnConfigDialog class.
# ABOUTME: It tests column visibility, reordering, and dialog interactions.
import unittest
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication, QListWidgetItem
from PyQt5.QtCore import Qt
import sys

# Import the dialog to test
from librarian_assistant.column_config_dialog import ColumnConfigDialog


class TestColumnConfigDialog(unittest.TestCase):
    """Test cases for ColumnConfigDialog."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_columns = ["id", "title", "author", "isbn", "pages", "publisher"]
        self.test_visible = ["id", "title", "author", "pages"]
        
    def test_dialog_initialization(self):
        """Test dialog initializes with correct columns and visibility."""
        dialog = ColumnConfigDialog(self.test_columns, self.test_visible)
        
        # Check window properties
        self.assertEqual(dialog.windowTitle(), "Configure Table Columns")
        self.assertTrue(dialog.isModal())
        
        # Check column list populated correctly
        self.assertEqual(dialog.column_list.count(), len(self.test_columns))
        
        # Check correct items are checked
        for i in range(dialog.column_list.count()):
            item = dialog.column_list.item(i)
            col_name = item.text()
            if col_name in self.test_visible:
                self.assertEqual(item.checkState(), Qt.Checked)
            else:
                self.assertEqual(item.checkState(), Qt.Unchecked)
        
        # Check all buttons exist
        self.assertIsNotNone(dialog.up_button)
        self.assertIsNotNone(dialog.down_button)
        self.assertIsNotNone(dialog.show_all_button)
        self.assertIsNotNone(dialog.hide_all_button)
    
    def test_dialog_initialization_all_visible(self):
        """Test dialog when no visible_columns provided (all visible)."""
        dialog = ColumnConfigDialog(self.test_columns)
        
        # All columns should be checked
        for i in range(dialog.column_list.count()):
            item = dialog.column_list.item(i)
            self.assertEqual(item.checkState(), Qt.Checked)
        
        # visible_columns should equal column_names
        self.assertEqual(dialog.visible_columns, dialog.column_names)
    
    def test_item_check_state_change(self):
        """Test changing item check state updates visible_columns."""
        dialog = ColumnConfigDialog(self.test_columns, self.test_visible)
        
        # Find and uncheck "title"
        for i in range(dialog.column_list.count()):
            item = dialog.column_list.item(i)
            if item.text() == "title":
                item.setCheckState(Qt.Unchecked)
                break
        
        self.assertNotIn("title", dialog.visible_columns)
        
        # Find and check "isbn"
        for i in range(dialog.column_list.count()):
            item = dialog.column_list.item(i)
            if item.text() == "isbn":
                item.setCheckState(Qt.Checked)
                break
        
        self.assertIn("isbn", dialog.visible_columns)
    
    def test_move_up_button(self):
        """Test moving item up in the list."""
        dialog = ColumnConfigDialog(self.test_columns)
        
        # Select "author" (index 2)
        dialog.column_list.setCurrentRow(2)
        
        # Should be able to move up
        self.assertTrue(dialog.up_button.isEnabled())
        
        # Move up
        dialog._move_up()
        
        # Check new order
        self.assertEqual(dialog.column_names[1], "author")
        self.assertEqual(dialog.column_names[2], "title")
        
        # Check list widget updated
        self.assertEqual(dialog.column_list.item(1).text(), "author")
        self.assertEqual(dialog.column_list.item(2).text(), "title")
        
        # Current row should follow the item
        self.assertEqual(dialog.column_list.currentRow(), 1)
    
    def test_move_down_button(self):
        """Test moving item down in the list."""
        dialog = ColumnConfigDialog(self.test_columns)
        
        # Select "title" (index 1)
        dialog.column_list.setCurrentRow(1)
        
        # Should be able to move down
        self.assertTrue(dialog.down_button.isEnabled())
        
        # Move down
        dialog._move_down()
        
        # Check new order
        self.assertEqual(dialog.column_names[1], "author")
        self.assertEqual(dialog.column_names[2], "title")
        
        # Check list widget updated
        self.assertEqual(dialog.column_list.item(1).text(), "author")
        self.assertEqual(dialog.column_list.item(2).text(), "title")
        
        # Current row should follow the item
        self.assertEqual(dialog.column_list.currentRow(), 2)
    
    def test_move_buttons_disabled_at_boundaries(self):
        """Test move buttons are disabled at list boundaries."""
        dialog = ColumnConfigDialog(self.test_columns)
        
        # Select first item
        dialog.column_list.setCurrentRow(0)
        self.assertFalse(dialog.up_button.isEnabled())
        self.assertTrue(dialog.down_button.isEnabled())
        
        # Select last item
        dialog.column_list.setCurrentRow(dialog.column_list.count() - 1)
        self.assertTrue(dialog.up_button.isEnabled())
        self.assertFalse(dialog.down_button.isEnabled())
        
        # No selection
        dialog.column_list.setCurrentRow(-1)
        self.assertFalse(dialog.up_button.isEnabled())
        self.assertFalse(dialog.down_button.isEnabled())
    
    def test_show_all_button(self):
        """Test Show All button checks all items."""
        dialog = ColumnConfigDialog(self.test_columns, ["id"])  # Only id visible
        
        dialog._show_all()
        
        # All items should be checked
        for i in range(dialog.column_list.count()):
            item = dialog.column_list.item(i)
            self.assertEqual(item.checkState(), Qt.Checked)
        
        # All columns should be in visible_columns
        self.assertEqual(set(dialog.visible_columns), set(self.test_columns))
    
    def test_hide_all_button(self):
        """Test Hide All button unchecks all items."""
        dialog = ColumnConfigDialog(self.test_columns)  # All visible
        
        dialog._hide_all()
        
        # All items should be unchecked
        for i in range(dialog.column_list.count()):
            item = dialog.column_list.item(i)
            self.assertEqual(item.checkState(), Qt.Unchecked)
        
        # visible_columns should be empty
        self.assertEqual(len(dialog.visible_columns), 0)
    
    def test_reset_button(self):
        """Test Reset button restores original configuration."""
        dialog = ColumnConfigDialog(self.test_columns, self.test_visible)
        
        # Make changes
        dialog._hide_all()
        dialog.column_list.setCurrentRow(0)
        dialog._move_down()
        
        # Verify changes were made
        self.assertEqual(len(dialog.visible_columns), 0)
        self.assertNotEqual(dialog.column_names, self.test_columns)
        
        # Reset
        dialog._reset_to_original()
        
        # Check original state restored
        self.assertEqual(dialog.column_names, self.test_columns)
        self.assertEqual(set(dialog.visible_columns), set(self.test_visible))
        
        # Check UI updated
        for i in range(dialog.column_list.count()):
            item = dialog.column_list.item(i)
            col_name = item.text()
            if col_name in self.test_visible:
                self.assertEqual(item.checkState(), Qt.Checked)
            else:
                self.assertEqual(item.checkState(), Qt.Unchecked)
    
    def test_default_button(self):
        """Test Default button restores all columns visible in original order."""
        # Start with some columns hidden
        dialog = ColumnConfigDialog(self.test_columns, self.test_visible)
        
        # Make changes
        dialog._hide_all()
        dialog.column_list.setCurrentRow(0)
        dialog._move_down()
        
        # Verify changes were made
        self.assertEqual(len(dialog.visible_columns), 0)
        self.assertNotEqual(dialog.column_names, self.test_columns)
        
        # Reset to default
        dialog._reset_to_default()
        
        # Check default state (all visible, original order)
        self.assertEqual(dialog.column_names, self.test_columns)
        self.assertEqual(dialog.visible_columns, self.test_columns)
        
        # Check UI updated - all should be checked
        for i in range(dialog.column_list.count()):
            item = dialog.column_list.item(i)
            self.assertEqual(item.checkState(), Qt.Checked)
    
    def test_accept_configuration_signal(self):
        """Test accepting configuration emits correct signal."""
        dialog = ColumnConfigDialog(self.test_columns, self.test_visible)
        
        # Create signal spy
        signal_spy = Mock()
        dialog.columns_configured.connect(signal_spy)
        
        # Make some changes
        dialog.column_list.setCurrentRow(1)
        dialog._move_down()
        
        # Find and check "publisher"
        for i in range(dialog.column_list.count()):
            item = dialog.column_list.item(i)
            if item.text() == "publisher":
                item.setCheckState(Qt.Checked)
                break
        
        # Accept
        dialog._accept_configuration()
        
        # Check signal was emitted with correct data
        signal_spy.assert_called_once()
        emitted_columns, emitted_visible = signal_spy.call_args[0]
        
        # Check column order changed
        self.assertEqual(emitted_columns[1], "author")
        self.assertEqual(emitted_columns[2], "title")
        
        # Check visible columns includes new check and maintains order
        self.assertIn("publisher", emitted_visible)
        # Visible columns should be in same order as column_names
        visible_indices = [emitted_columns.index(col) for col in emitted_visible]
        self.assertEqual(visible_indices, sorted(visible_indices))
    
    def test_cancel_does_not_emit_signal(self):
        """Test canceling dialog does not emit configuration signal."""
        dialog = ColumnConfigDialog(self.test_columns, self.test_visible)
        
        # Create signal spy
        signal_spy = Mock()
        dialog.columns_configured.connect(signal_spy)
        
        # Make changes and cancel
        dialog._hide_all()
        dialog.reject()
        
        # Signal should not have been emitted
        signal_spy.assert_not_called()


if __name__ == '__main__':
    unittest.main()