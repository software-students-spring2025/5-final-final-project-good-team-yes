import unittest
from app import app
import json
from unittest.mock import patch, MagicMock

class AppTestCase(unittest.TestCase):

    def setUp(self):
        """Set up test client and other test variables."""
        self.client = app.test_client()
        self.client.testing = True 

    def test_home_status_code(self, mock_collection):
        """Test that the single-page application loads successfully."""
        mock_collection.find.return_value = [] 
        result = self.client.get('/')
        self.assertEqual(result.status_code, 200)

    @patch('app.collection')
    def test_get_sandwiches_api(self, mock_collection):
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
        mock_collection.find.return_value = mock_cursor
        
        # Call the API endpoint
        response = self.client.get('/api/sandwiches')
        
        # Assert the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test Deli')

    @patch('app.collection')
    def test_get_sandwiches_with_price_filter(self, mock_collection):
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
        mock_collection.find.return_value = mock_cursor
        
        # Call the API endpoint with price filters
        response = self.client.get('/api/sandwiches?min_price=5&max_price=7')
        
        # Assert the response
        self.assertEqual(response.status_code, 200)
        
        # Verify that the correct query was used
        mock_collection.find.assert_called_once()
        args, kwargs = mock_collection.find.call_args
        self.assertEqual(kwargs.get('projection'), {'_id': 0})
        query = args[0]
        self.assertIn('price', query)
        self.assertEqual(query['price']['$lte'], 7.0)
        self.assertEqual(query['price']['$gte'], 5.0)
    
    @patch("app.geocode_with_local_database")
    def test_geocode_local_success(self, mock_local):
        """ Test PRE API geocode endpoint"""
        mock_local.return_value = {
            "lat": 40.7128,
            "lon": -74.0060,
            "display_name": "Mock Address",
            "provider": "local_db"
        }
        response = self.client.get("/api/geocode?address=123+Fake+St")
        self.assertEqual(response.status_code, 200)
        self.assertIn("lat", response.get_json())

    @patch('app.collection')
    def test_add_sandwich_api(self, mock_collection):
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
        mock_collection.insert_one.return_value = MagicMock()
        
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
        mock_collection.insert_one.assert_called_once()
        call_args = mock_collection.insert_one.call_args[0][0]
        self.assertEqual(call_args['name'], 'New Deli')
        self.assertEqual(call_args['address'], '456 New St, Brooklyn, New York, NY 10001, United States')
        self.assertEqual(call_args['price'], 6.99)

    @patch("app.collection")
    def test_get_nearby_sandwiches(self, mock_collection):
        mock_data = [
            {"name": "Nearby Deli", "lat": 40.713, "lon": -74.006, "price": 6.5}
        ]
        mock_collection.find.return_value = mock_data
        response = self.client.get("/api/sandwiches/nearby?lat=40.7128&lon=-74.0060")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    

if __name__ == '__main__':
    unittest.main() 