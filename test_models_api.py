import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

def test_models_api():
    # Test data
    test_model = {
        "id": 1,
        "name": "Test Model",
        "description": "A test model for API validation",
        "customHeader": '{"Authorization": "Bearer token"}',
        "url": "https://api.example.com/v1/chat/completions",
        "otherParams": '{"model": "gpt-3.5-turbo", "temperature": 0.7}'
    }
    
    # Test creating a model
    print("Testing model creation...")
    response = requests.post(f"{BASE_URL}/models", json=test_model)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test getting all models
    print("\nTesting getting all models...")
    response = requests.get(f"{BASE_URL}/models")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test updating a model
    print("\nTesting model update...")
    updated_model = test_model.copy()
    updated_model["description"] = "Updated description"
    response = requests.put(f"{BASE_URL}/models/1", json=updated_model)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test getting all models again to verify update
    print("\nTesting getting all models after update...")
    response = requests.get(f"{BASE_URL}/models")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test deleting a model
    print("\nTesting model deletion...")
    response = requests.delete(f"{BASE_URL}/models/1")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test getting all models again to verify deletion
    print("\nTesting getting all models after deletion...")
    response = requests.get(f"{BASE_URL}/models")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    test_models_api()