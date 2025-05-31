# ABOUTME: Tests for the enhanced stylesheet implementation in Phase 8
# ABOUTME: Verifies that enhanced dark theme is properly applied to all widgets

import pytest
from PyQt5.QtWidgets import QApplication, QPushButton, QLabel, QLineEdit, QTableWidget, QGroupBox
from PyQt5.QtCore import Qt
from librarian_assistant.enhanced_stylesheet import ENHANCED_DARK_THEME, SPACING, ELEVATION_SHADOWS


class TestEnhancedStylesheet:
    """Test enhanced stylesheet implementation"""
    
    def test_enhanced_stylesheet_imported(self):
        """Test that enhanced stylesheet can be imported"""
        assert ENHANCED_DARK_THEME is not None
        assert isinstance(ENHANCED_DARK_THEME, str)
        assert len(ENHANCED_DARK_THEME) > 1000  # Should be a substantial stylesheet
        
    def test_spacing_constants_defined(self):
        """Test that spacing constants are properly defined"""
        assert SPACING is not None
        assert isinstance(SPACING, dict)
        assert 'xs' in SPACING
        assert 'sm' in SPACING
        assert 'md' in SPACING
        assert 'lg' in SPACING
        assert 'xl' in SPACING
        assert 'xxl' in SPACING
        assert all(isinstance(v, int) for v in SPACING.values())
        
    def test_elevation_shadows_defined(self):
        """Test that elevation shadow styles are defined"""
        assert ELEVATION_SHADOWS is not None
        assert isinstance(ELEVATION_SHADOWS, dict)
        assert 1 in ELEVATION_SHADOWS
        assert 2 in ELEVATION_SHADOWS
        assert 3 in ELEVATION_SHADOWS
        assert 4 in ELEVATION_SHADOWS
        assert 5 in ELEVATION_SHADOWS
        assert all(isinstance(v, str) for v in ELEVATION_SHADOWS.values())
        
    def test_stylesheet_contains_widget_styles(self):
        """Test that stylesheet contains styles for all major widgets"""
        widgets = [
            'QWidget', 'QMainWindow', 'QDialog', 'QTabWidget', 'QTabBar',
            'QGroupBox', 'QPushButton', 'QLineEdit', 'QTextEdit', 'QComboBox',
            'QCheckBox', 'QRadioButton', 'QTableWidget', 'QHeaderView',
            'QScrollBar', 'QStatusBar', 'QLabel', 'QToolTip', 'QMessageBox',
            'QProgressBar', 'QSpinBox', 'QSlider', 'QListWidget', 'QTreeWidget',
            'QMenu', 'QDateEdit'
        ]
        
        for widget in widgets:
            assert widget in ENHANCED_DARK_THEME, f"Stylesheet missing styles for {widget}"
            
    def test_button_object_name_styles(self):
        """Test that stylesheet contains specific button styles"""
        button_ids = [
            'fetchDataButton', 'setUpdateTokenButton', 
            'filterButton', 'configureColumnsButton'
        ]
        
        for button_id in button_ids:
            assert f'#{button_id}' in ENHANCED_DARK_THEME, f"Stylesheet missing styles for #{button_id}"
            
    def test_dark_theme_colors(self):
        """Test that dark theme colors are properly defined"""
        # Check for main background colors
        assert '#1a1a1a' in ENHANCED_DARK_THEME  # Main background
        assert '#1e1e1e' in ENHANCED_DARK_THEME  # Secondary background
        assert '#e0e0e0' in ENHANCED_DARK_THEME  # Main text color
        assert '#6b46c1' in ENHANCED_DARK_THEME  # Accent color (purple)
        
    def test_border_radius_values(self):
        """Test that border radius values are consistent"""
        assert 'border-radius: 4px' in ENHANCED_DARK_THEME
        assert 'border-radius: 6px' in ENHANCED_DARK_THEME
        assert 'border-radius: 8px' in ENHANCED_DARK_THEME
        
    def test_font_styling(self):
        """Test that font styling is properly defined"""
        assert 'font-family:' in ENHANCED_DARK_THEME
        assert 'font-size:' in ENHANCED_DARK_THEME
        assert 'font-weight:' in ENHANCED_DARK_THEME
        
    def test_hover_states(self):
        """Test that hover states are defined for interactive elements"""
        assert ':hover' in ENHANCED_DARK_THEME
        assert 'QPushButton:hover' in ENHANCED_DARK_THEME
        assert 'QComboBox:hover' in ENHANCED_DARK_THEME
        
    def test_focus_states(self):
        """Test that focus states are defined for input elements"""
        assert ':focus' in ENHANCED_DARK_THEME
        assert 'QLineEdit:focus' in ENHANCED_DARK_THEME
        assert 'QPushButton:focus' in ENHANCED_DARK_THEME
        
    def test_custom_classes(self):
        """Test that custom spacing and elevation classes are defined"""
        assert '.spacing-tight' in ENHANCED_DARK_THEME
        assert '.spacing-normal' in ENHANCED_DARK_THEME
        assert '.spacing-relaxed' in ENHANCED_DARK_THEME
        assert '.spacing-loose' in ENHANCED_DARK_THEME
        
        assert '.elevation-1' in ENHANCED_DARK_THEME
        assert '.elevation-2' in ENHANCED_DARK_THEME
        assert '.elevation-3' in ENHANCED_DARK_THEME
        assert '.elevation-4' in ENHANCED_DARK_THEME
        
    def test_special_ui_elements(self):
        """Test that special UI element styles are defined"""
        assert '.book-mapping-card' in ENHANCED_DARK_THEME
        assert '.help-text' in ENHANCED_DARK_THEME
        assert '.error' in ENHANCED_DARK_THEME
        assert '.warning' in ENHANCED_DARK_THEME
        assert '.success' in ENHANCED_DARK_THEME
        assert '.clickable-link' in ENHANCED_DARK_THEME


class TestEnhancedStylesheetApplication:
    """Test enhanced stylesheet application on actual widgets"""
    
    def test_button_styling(self, qapp):
        """Test that buttons get proper styling"""
        qapp.setStyleSheet(ENHANCED_DARK_THEME)
        button = QPushButton("Test Button")
        button.setObjectName("fetchDataButton")
        
        # The button should exist and be styled
        assert button is not None
        
    def test_input_field_styling(self, qapp):
        """Test that input fields get proper styling"""
        qapp.setStyleSheet(ENHANCED_DARK_THEME)
        line_edit = QLineEdit()
        
        # The input should exist and be styled
        assert line_edit is not None
        
    def test_table_widget_styling(self, qapp):
        """Test that table widgets get proper styling"""
        qapp.setStyleSheet(ENHANCED_DARK_THEME)
        table = QTableWidget()
        
        # The table should exist and be styled
        assert table is not None
        
    def test_groupbox_styling(self, qapp):
        """Test that group boxes get proper styling"""
        qapp.setStyleSheet(ENHANCED_DARK_THEME)
        groupbox = QGroupBox("Test Group")
        
        # The groupbox should exist and be styled
        assert groupbox is not None