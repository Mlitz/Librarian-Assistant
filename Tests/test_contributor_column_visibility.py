# ABOUTME: This file contains tests for the refined contributor column visibility logic.
# ABOUTME: It verifies that only necessary contributor columns are shown.
import unittest
from unittest.mock import Mock, patch
from librarian_assistant.main import MainWindow


class TestContributorColumnVisibility(unittest.TestCase):
    """Test cases for refined contributor column visibility."""
    
    def setUp(self):
        """Set up test environment."""
        self.window = MainWindow()
    
    def test_contributor_column_generation_exact_count(self):
        """Test that only the necessary number of contributor columns are created."""
        # Test data with varying numbers of contributors per role
        test_editions = [
            {
                'id': 1,
                'cached_contributors': [
                    {'contribution': None, 'author': {'name': 'Primary Author'}},
                    {'contribution': 'Author', 'author': {'name': 'Secondary Author'}},
                    {'contribution': 'Narrator', 'author': {'name': 'Narrator 1'}},
                    {'contribution': 'Narrator', 'author': {'name': 'Narrator 2'}},
                    {'contribution': 'Narrator', 'author': {'name': 'Narrator 3'}}
                ]
            },
            {
                'id': 2,
                'cached_contributors': [
                    {'contribution': None, 'author': {'name': 'Only Author'}},
                    {'contribution': 'Editor', 'author': {'name': 'Editor 1'}}
                ]
            },
            {
                'id': 3,
                'cached_contributors': [
                    {'contribution': None, 'author': {'name': 'Another Author'}},
                    {'contribution': 'Translator', 'author': {'name': 'Translator 1'}},
                    {'contribution': 'Translator', 'author': {'name': 'Translator 2'}}
                ]
            }
        ]
        
        # Process contributor data
        result = self.window._process_contributor_data(test_editions)
        
        # Verify active roles
        self.assertIn('Author', result['active_roles'])
        self.assertIn('Narrator', result['active_roles'])
        self.assertIn('Editor', result['active_roles'])
        self.assertIn('Translator', result['active_roles'])
        
        # Verify max contributors per role
        max_contributors = result['max_contributors_per_role']
        self.assertEqual(max_contributors.get('Author', 0), 2)  # Primary + Secondary
        self.assertEqual(max_contributors.get('Narrator', 0), 3)  # 3 narrators in edition 1
        self.assertEqual(max_contributors.get('Editor', 0), 1)  # 1 editor in edition 2
        self.assertEqual(max_contributors.get('Translator', 0), 2)  # 2 translators in edition 3
    
    def test_no_illustrator_columns_when_none_exist(self):
        """Test that roles with no contributors don't get columns."""
        # Test data with no illustrators
        test_editions = [
            {
                'id': 1,
                'cached_contributors': [
                    {'contribution': None, 'author': {'name': 'Author 1'}},
                    {'contribution': 'Editor', 'author': {'name': 'Editor 1'}}
                ]
            }
        ]
        
        result = self.window._process_contributor_data(test_editions)
        
        # Verify Illustrator is not in active roles
        self.assertNotIn('Illustrator', result['active_roles'])
        
        # Verify only Author and Editor are active
        self.assertEqual(set(result['active_roles']), {'Author', 'Editor'})
    
    def test_single_contributor_gets_one_column(self):
        """Test that a role with only one contributor gets only one column."""
        test_editions = [
            {
                'id': 1,
                'cached_contributors': [
                    {'contribution': None, 'author': {'name': 'Solo Author'}},
                    {'contribution': 'Cover Artist', 'author': {'name': 'Artist Name'}}
                ]
            }
        ]
        
        result = self.window._process_contributor_data(test_editions)
        
        # Verify single contributor counts
        max_contributors = result['max_contributors_per_role']
        self.assertEqual(max_contributors.get('Author', 0), 1)
        self.assertEqual(max_contributors.get('Cover Artist', 0), 1)
    
    def tearDown(self):
        """Clean up after tests."""
        self.window.close()


if __name__ == '__main__':
    unittest.main()