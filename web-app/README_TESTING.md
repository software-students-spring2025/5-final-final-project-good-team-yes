# Testing the NYC Sandwich Price Tracker

This document provides information on how to properly run tests for the NYC Sandwich Price Tracker application.

## Running Tests Locally

The application uses pytest for testing. The tests in `test_app.py` use mocking to prevent actual connections to MongoDB during testing.

To run tests locally:

```bash
cd web-app
# Set invalid MongoDB URI to ensure no real database connections
MONGO_URI="mongodb://nonexistent-host:27017" MONGO_DB="test_sandwich_db" python -m pytest test_app.py -v
```

For test coverage:

```bash
cd web-app
MONGO_URI="mongodb://nonexistent-host:27017" MONGO_DB="test_sandwich_db" python -m pytest test_app.py -v --cov=app
```

## Ensuring Tests Do Not Access Real Database

Our tests use two mechanisms to prevent connecting to a real database:

1. **Mock MongoDB Connection**: Python's `unittest.mock` library is used to mock the MongoDB connection. This intercepts and simulates all MongoDB operations.

2. **Invalid MongoDB URI**: For additional safety, we set the `MONGO_URI` environment variable to an invalid/nonexistent URI, which would cause an error if any unmocked MongoDB connection is attempted.

## Troubleshooting

If you suspect tests might be accessing a real database:

1. Make sure you're running tests with the `MONGO_URI` environment variable set to a non-existent URI
2. Ensure that the `MongoClient` is properly mocked in test setup
3. Verify that all MongoDB operations in tests use the mock objects and not real connections

## Running Tests with PowerShell

In PowerShell, set the environment variables before running tests:

```powershell
# Set temporarily for the current session
$env:MONGO_URI = "mongodb://nonexistent-host:27017"
$env:MONGO_DB = "test_sandwich_db"
cd web-app
python -m pytest test_app.py -v
```

## GitHub Actions Integration

The project includes GitHub Actions workflows to automatically run tests on push and pull requests. These workflows:

1. Set up a Python environment
2. Install all required dependencies
3. Set the necessary environment variables to invalid/test values to ensure tests don't access a real database
4. Run the tests with coverage reporting 