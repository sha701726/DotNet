#!/usr/bin/env python3
"""
Test script for AmLI Chatbot functionality
Tests job applications, certificate searches, and general AmLI responses
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_amli_chatbot():
    """Test the AmLI chatbot functionality"""
    
    print("🧪 Testing AmLI Chatbot Functionality")
    print("=" * 50)
    
    # Test 1: General AmLI information
    print("\n1. Testing General AmLI Information...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "message": "Tell me about AmLI services"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data['response'][:100]}...")
        print(f"   Type: {data['type']}")
    else:
        print(f"❌ Error: {response.status_code}")
    
    # Test 2: Job Application Request
    print("\n2. Testing Job Application Request...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "message": "I want to apply for a job at AmLI",
        "intent": "job_application"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data['response'][:100]}...")
        print(f"   Type: {data['type']}")
        print(f"   Form URL: {data.get('form_url', 'N/A')}")
    else:
        print(f"❌ Error: {response.status_code}")
    
    # Test 3: Certificate Search Request
    print("\n3. Testing Certificate Search Request...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "message": "I want to find my certificate",
        "intent": "certificate_search"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data['response'][:100]}...")
        print(f"   Type: {data['type']}")
    else:
        print(f"❌ Error: {response.status_code}")
    
    # Test 4: Certificate Search with Enrollment Number
    print("\n4. Testing Certificate Search with Enrollment Number...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "message": "Search for certificate with enrollment 123456",
        "intent": "certificate_search",
        "enrollment_no": "123456"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data['response'][:100]}...")
        print(f"   Type: {data['type']}")
        print(f"   Enrollment: {data.get('enrollment_no', 'N/A')}")
    else:
        print(f"❌ Error: {response.status_code}")
    
    # Test 5: Password Verification
    print("\n5. Testing Password Verification...")
    response = requests.post(f"{BASE_URL}/chat", json={
        "message": "Verify password 654321",
        "intent": "verify_password",
        "enrollment_no": "123456",
        "password": "654321"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data['response'][:100]}...")
        print(f"   Type: {data['type']}")
    else:
        print(f"❌ Error: {response.status_code}")
    
    # Test 6: Home Page
    print("\n6. Testing Home Page...")
    response = requests.get(f"{BASE_URL}/")
    
    if response.status_code == 200:
        print("✅ Home page loads successfully")
        if "AmLI" in response.text:
            print("✅ AmLI branding found on page")
        else:
            print("⚠️  AmLI branding not found")
    else:
        print(f"❌ Error: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎯 AmLI Chatbot Testing Complete!")
    print("\nTo test the full functionality:")
    print("1. Open http://localhost:5000 in your browser")
    print("2. Try the quick action buttons")
    print("3. Test job applications and certificate searches")
    print("4. Verify Supabase integration (if configured)")

if __name__ == "__main__":
    try:
        test_amli_chatbot()
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the AmLI chatbot is running on http://localhost:5000")
        print("   Run: python bot.py")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
