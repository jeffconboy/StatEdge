#!/usr/bin/env python3
"""
Test Betting Service
===================

Simple test script to verify the betting service is working correctly.
"""

import asyncio
import requests
import json
from datetime import datetime, date

# Service configuration
BETTING_SERVICE_URL = "http://localhost:18002"

def test_health_check():
    """Test service health check"""
    print("🏥 Testing health check...")
    try:
        response = requests.get(f"{BETTING_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_root_endpoint():
    """Test root endpoint"""
    print("\n🏠 Testing root endpoint...")
    try:
        response = requests.get(f"{BETTING_SERVICE_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint working: {data.get('message', 'N/A')}")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False

def test_api_docs():
    """Test API documentation"""
    print("\n📚 Testing API docs...")
    try:
        response = requests.get(f"{BETTING_SERVICE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API docs accessible")
            return True
        else:
            print(f"❌ API docs failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API docs error: {e}")
        return False

def test_todays_games():
    """Test today's games endpoint"""
    print("\n⚾ Testing today's games...")
    try:
        response = requests.get(f"{BETTING_SERVICE_URL}/api/games/today", timeout=10)
        if response.status_code == 200:
            data = response.json()
            games_count = len(data.get('games', []))
            print(f"✅ Today's games endpoint working: {games_count} games found")
            return True
        else:
            print(f"❌ Today's games failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Today's games error: {e}")
        return False

def test_create_sample_bet():
    """Test creating a sample bet"""
    print("\n🎯 Testing bet creation...")
    try:
        sample_bet = {
            "game_id": f"20250726_TEST@SAMPLE",
            "home_team": "SAMPLE",
            "away_team": "TEST",
            "game_date": date.today().isoformat(),
            "bet_type": "moneyline",
            "bet_side": "home",
            "bet_amount": 25.00,
            "odds": -150,
            "confidence_level": 7,
            "prediction_reasoning": "Test bet for service verification"
        }
        
        response = requests.post(
            f"{BETTING_SERVICE_URL}/api/bets/",
            json=sample_bet,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            bet_id = data.get('id')
            print(f"✅ Bet created successfully: ID {bet_id}")
            return bet_id
        else:
            print(f"❌ Bet creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Bet creation error: {e}")
        return None

def test_get_betting_history():
    """Test getting betting history"""
    print("\n📊 Testing betting history...")
    try:
        response = requests.get(f"{BETTING_SERVICE_URL}/api/bets/?limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            bet_count = len(data)
            print(f"✅ Betting history working: {bet_count} bets retrieved")
            return True
        else:
            print(f"❌ Betting history failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Betting history error: {e}")
        return False

def test_analytics():
    """Test analytics endpoints"""
    print("\n📈 Testing analytics...")
    try:
        response = requests.get(f"{BETTING_SERVICE_URL}/api/analytics/summary", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Analytics working: {data.get('total_bets', 0)} total bets")
            return True
        else:
            print(f"❌ Analytics failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Analytics error: {e}")
        return False

def run_all_tests():
    """Run all service tests"""
    print("🧪 Starting Betting Service Tests")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Root Endpoint", test_root_endpoint),
        ("API Documentation", test_api_docs),
        ("Today's Games", test_todays_games),
        ("Betting History", test_get_betting_history),
        ("Analytics", test_analytics),
        ("Create Sample Bet", test_create_sample_bet)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Betting service is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the service configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)