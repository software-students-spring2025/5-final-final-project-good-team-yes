import unittest
from app import app
import json
from unittest.mock import patch, MagicMock

class AppTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up test client and mock MongoDB connection."""
        # Mock MongoDB client and collection
        cls.mongo_patcher = patch('app.MongoClient')
        cls.mock_mongo = cls.mongo_patcher.start()
        
        # Create a mock collection
        cls.mock_collection = MagicMock()
        cls.mock_mongo.return_value.__getitem__.return_value.__getitem__.return_value = cls.mock_collection
        
        # Set up test client
        cls.client = app.test_client()
        cls.client.testing = True

    @classmethod
    def tearDownClass(cls):
        """Clean up after tests."""
        cls.mongo_patcher.stop()

    def setUp(self):
        """Set up test variables."""
        # Reset mock collection for each test
        self.mock_collection.reset_mock()

    def test_home_status_code(self):
        """Test that the single-page application loads successfully."""
        result = self.client.get('/')
        self.assertEqual(result.status_code, 200)

    def test_get_sandwiches_api(self):
        """Test the GET sandwiches API endpoint."""
        # Mock data to return
        mock_data = [
            {
                "name": "Test Deli",
                "address": "123 Test St, New York, NY",
                "lat": 40.7128,
                "lon": -74.0060,
                "price": 5.99
            }
        ]
        
        # Configure the mock to return the sample data
        mock_cursor = MagicMock()
        mock_cursor.__iter__.return_value = mock_data
        self.mock_collection.find.return_value = mock_cursor
        
        # Call the API endpoint
        response = self.client.get('/api/sandwiches')
        
        # Assert the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test Deli')

    def test_get_sandwiches_with_price_filter(self):
        """Test the GET sandwiches API endpoint with price filters."""
        # Mock data to return
        mock_data = [
            {
                "name": "Test Deli",
                "address": "123 Test St, New York, NY",
                "lat": 40.7128,
                "lon": -74.0060,
                "price": 5.99
            }
        ]
        
        # Configure the mock to return the sample data
        mock_cursor = MagicMock()
        mock_cursor.__iter__.return_value = mock_data
        self.mock_collection.find.return_value = mock_cursor
        
        # Call the API endpoint with price filters
        response = self.client.get('/api/sandwiches?min_price=5&max_price=7')
        
        # Assert the response
        self.assertEqual(response.status_code, 200)
        
        # Verify that the correct query was used
        self.mock_collection.find.assert_called_once()
        args, kwargs = self.mock_collection.find.call_args
        self.assertEqual(kwargs.get('projection'), {'_id': 0})
        query = args[0]
        self.assertIn('price', query)
        self.assertEqual(query['price']['$lte'], 7.0)
        self.assertEqual(query['price']['$gte'], 5.0)

    def test_add_sandwich_api(self):
        """Test the POST sandwiches API endpoint."""
        # Sample data to send - now with pre-geocoded address
        sandwich_data = {
            "name": "New Deli",
            "address": "456 New St, Brooklyn, New York, NY 10001, United States",
            "lat": 40.7200,
            "lon": -74.0100,
            "price": 6.99
        }
        
        # Configure the mock
        self.mock_collection.insert_one.return_value = MagicMock()
        
        # Call the API endpoint
        response = self.client.post(
            '/api/sandwiches',
            data=json.dumps(sandwich_data),
            content_type='application/json'
        )
        
        # Assert the response
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify the mock was called with the expected data
        self.mock_collection.insert_one.assert_called_once()
        call_args = self.mock_collection.insert_one.call_args[0][0]
        self.assertEqual(call_args['name'], 'New Deli')
        self.assertEqual(call_args['address'], '456 New St, Brooklyn, New York, NY 10001, United States')
        self.assertEqual(call_args['price'], 6.99)

if __name__ == '__main__':
    unittest.main() 