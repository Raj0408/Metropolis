#!/usr/bin/env python3
"""
Test script for Metropolis AI Platform API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api():
    print("🚀 Testing Metropolis AI Platform API")
    print("=" * 50)
    
    try:
        # 1. Test health endpoint
        print("\n1. Testing health endpoint...")
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.text}")
            return
        
        # 2. Test API documentation
        print("\n2. Testing API documentation...")
        response = requests.get(f"{BASE_URL}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ API documentation accessible")
        else:
            print(f"❌ API documentation failed: {response.status_code}")
        
        # 3. Test user creation (without authentication for now)
        print("\n3. Testing user creation...")
        user_data = {
            "email": "test@metropolis.ai",
            "username": "testuser",
            "password": "testpass123"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/users", json=user_data, timeout=10)
            print(f"User creation status: {response.status_code}")
            if response.status_code == 201:
                user = response.json()
                print(f"✅ User created successfully: {user['username']}")
            else:
                print(f"❌ User creation failed: {response.text}")
        except Exception as e:
            print(f"❌ User creation error: {e}")
        
        # 4. Test workflows endpoint
        print("\n4. Testing workflows endpoint...")
        try:
            response = requests.get(f"{BASE_URL}/api/workflows", timeout=10)
            print(f"Workflows status: {response.status_code}")
            if response.status_code in [200, 401]:  # 401 is expected without auth
                print("✅ Workflows endpoint accessible")
            else:
                print(f"❌ Workflows endpoint failed: {response.text}")
        except Exception as e:
            print(f"❌ Workflows error: {e}")
        
        print("\n🎉 API test completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running.")
        print("Run: docker-compose up --build")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_api()
