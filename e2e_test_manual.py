#!/usr/bin/env python3
"""
Manual E2E Test Script for StatEdge Frontend-Database Connection
================================================================

This script tests the complete data flow from database → backend → frontend
"""
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import time
from datetime import datetime

# Test Configuration
FRONTEND_URL = "http://localhost:3002"
BACKEND_URLS = {
    "python": "http://localhost:18001",
    "node": "http://localhost:3001"
}
DB_URL = "postgresql://sports_user:sports_secure_2025@localhost:5432/sports_data"

class StatEdgeE2ETest:
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def log_test(self, test_name, status, message=""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if status == "PASS":
            print(f"✅ {test_name}: {message}")
            self.passed += 1
        else:
            print(f"❌ {test_name}: {message}")
            self.failed += 1
    
    def test_database_connection(self):
        """Test 1: Direct database connectivity"""
        try:
            conn = psycopg2.connect(DB_URL)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Test MLB data exists
            cursor.execute("SELECT COUNT(*) as count FROM mlb_teams")
            teams_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM mlb_players")
            players_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM mlb_game_details")
            games_count = cursor.fetchone()['count']
            
            cursor.close()
            conn.close()
            
            if teams_count > 0 and players_count > 0:
                self.log_test("Database Connection", "PASS", 
                             f"Teams: {teams_count}, Players: {players_count}, Games: {games_count}")
            else:
                self.log_test("Database Connection", "FAIL", "No MLB data found")
                
        except Exception as e:
            self.log_test("Database Connection", "FAIL", str(e))
    
    def test_backend_apis(self):
        """Test 2: Backend API endpoints"""
        for backend_name, base_url in BACKEND_URLS.items():
            try:
                # Test health endpoint
                response = requests.get(f"{base_url}/health", timeout=5)
                if response.status_code == 200:
                    self.log_test(f"{backend_name.title()} Backend Health", "PASS", "API responding")
                else:
                    self.log_test(f"{backend_name.title()} Backend Health", "FAIL", 
                                 f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"{backend_name.title()} Backend Health", "FAIL", str(e))
    
    def test_data_endpoints(self):
        """Test 3: Data-specific API endpoints"""
        # Test Python backend endpoints
        python_endpoints = [
            "/api/players/trending",
            "/api/live-games",
            "/api/league-stats/leaders/batting"
        ]
        
        for endpoint in python_endpoints:
            try:
                response = requests.get(f"{BACKEND_URLS['python']}{endpoint}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    data_count = len(data) if isinstance(data, list) else len(data.keys())
                    self.log_test(f"Python API {endpoint}", "PASS", f"Returned {data_count} items")
                else:
                    self.log_test(f"Python API {endpoint}", "FAIL", f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Python API {endpoint}", "FAIL", str(e))
    
    def test_frontend_accessibility(self):
        """Test 4: Frontend accessibility"""
        try:
            response = requests.get(FRONTEND_URL, timeout=10)
            if response.status_code == 200:
                if "StatEdge" in response.text or "react" in response.text.lower():
                    self.log_test("Frontend Accessibility", "PASS", "Frontend loading successfully")
                else:
                    self.log_test("Frontend Accessibility", "FAIL", "Frontend content unexpected")
            else:
                self.log_test("Frontend Accessibility", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Frontend Accessibility", "FAIL", str(e))
    
    def test_data_flow_integration(self):
        """Test 5: End-to-end data flow"""
        try:
            # Get data from database
            conn = psycopg2.connect(DB_URL)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT full_name FROM mlb_players LIMIT 5")
            db_players = [row['full_name'] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            
            # Get data from API
            response = requests.get(f"{BACKEND_URLS['python']}/api/players/trending", timeout=10)
            if response.status_code == 200:
                api_data = response.json()
                
                # Check if we have matching data structure
                if isinstance(api_data, list) and len(api_data) > 0:
                    self.log_test("Data Flow Integration", "PASS", 
                                 f"Database has {len(db_players)} players, API returning data")
                else:
                    self.log_test("Data Flow Integration", "FAIL", "API not returning expected data format")
            else:
                self.log_test("Data Flow Integration", "FAIL", "API endpoint not accessible")
                
        except Exception as e:
            self.log_test("Data Flow Integration", "FAIL", str(e))
    
    def test_mlb_data_freshness(self):
        """Test 6: MLB data freshness"""
        try:
            conn = psycopg2.connect(DB_URL)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check when data was last updated
            cursor.execute("""
                SELECT MAX(created_at) as last_update 
                FROM mlb_game_details 
                WHERE created_at IS NOT NULL
            """)
            result = cursor.fetchone()
            
            if result and result['last_update']:
                time_diff = datetime.now() - result['last_update'].replace(tzinfo=None)
                hours_old = time_diff.total_seconds() / 3600
                
                if hours_old < 24:
                    self.log_test("MLB Data Freshness", "PASS", 
                                 f"Data updated {hours_old:.1f} hours ago")
                else:
                    self.log_test("MLB Data Freshness", "WARN", 
                                 f"Data is {hours_old:.1f} hours old")
            else:
                self.log_test("MLB Data Freshness", "FAIL", "No timestamp data found")
                
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.log_test("MLB Data Freshness", "FAIL", str(e))
    
    def run_all_tests(self):
        """Run complete E2E test suite"""
        print("🚀 Starting StatEdge E2E Tests")
        print("=" * 50)
        
        self.test_database_connection()
        self.test_backend_apis()
        self.test_data_endpoints()
        self.test_frontend_accessibility()
        self.test_data_flow_integration()
        self.test_mlb_data_freshness()
        
        # Summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results Summary:")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {(self.passed/(self.passed+self.failed)*100):.1f}%")
        
        if self.failed == 0:
            print("\n🎉 All tests passed! Frontend-Database connection is working perfectly!")
        else:
            print(f"\n⚠️  {self.failed} tests failed. Check the issues above.")
        
        return self.test_results

if __name__ == "__main__":
    tester = StatEdgeE2ETest()
    results = tester.run_all_tests()
    
    # Save results
    with open('/home/jeffreyconboy/StatEdge/e2e_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Full test results saved to: e2e_test_results.json")