import requests
import sys
import json
import time
from datetime import datetime
import tempfile
import os

class MedIntelAPITester:
    def __init__(self, base_url="https://medreport-ai-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = None
        self.user_id = f"test_user_{int(time.time())}"

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers={'Content-Type': 'application/json'})
            elif method == 'POST':
                if files:
                    # For file uploads, don't set Content-Type header
                    response = requests.post(url, data=data, files=files)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers={'Content-Type': 'application/json'})

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic health check endpoint"""
        return self.run_test("Health Check", "GET", "", 200)

    def test_api_root(self):
        """Test API root endpoint"""
        return self.run_test("API Root", "GET", "", 200)

    def test_create_session(self):
        """Test creating a new chat session"""
        success, response = self.run_test(
            "Create Chat Session",
            "POST",
            "chat/session",
            200,
            data={
                "user_id": self.user_id,
                "language": "english"
            }
        )
        if success and 'id' in response:
            self.session_id = response['id']
            print(f"   Created session ID: {self.session_id}")
            return True
        return False

    def test_get_session(self):
        """Test getting session details"""
        if not self.session_id:
            print("❌ No session ID available for testing")
            return False
        
        return self.run_test(
            "Get Session Details",
            "GET",
            f"chat/session/{self.session_id}",
            200
        )[0]

    def test_send_message(self):
        """Test sending a text message"""
        if not self.session_id:
            print("❌ No session ID available for testing")
            return False
        
        success, response = self.run_test(
            "Send Text Message",
            "POST",
            "chat/message",
            200,
            data={
                "session_id": self.session_id,
                "message": "What does high blood pressure mean?",
                "language": "english"
            }
        )
        
        if success:
            # Check if AI response contains medical disclaimer
            ai_message = response.get('assistant_message', {}).get('content', '')
            if 'MEDICAL DISCLAIMER' in ai_message or 'informational purposes' in ai_message:
                print("✅ AI response includes medical disclaimer")
            else:
                print("⚠️  AI response may be missing medical disclaimer")
        
        return success

    def test_get_messages(self):
        """Test getting session messages"""
        if not self.session_id:
            print("❌ No session ID available for testing")
            return False
        
        return self.run_test(
            "Get Session Messages",
            "GET",
            f"chat/session/{self.session_id}/messages",
            200
        )[0]

    def test_file_upload(self):
        """Test file upload functionality"""
        if not self.session_id:
            print("❌ No session ID available for testing")
            return False
        
        # Create a test text file
        test_content = "Patient: John Doe\nAge: 45\nBlood Pressure: 140/90 mmHg\nCholesterol: 220 mg/dL\nDiagnosis: Hypertension"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test_report.txt', f, 'text/plain')}
                data = {
                    'session_id': self.session_id,
                    'message': 'Please analyze this medical report',
                    'language': 'english'
                }
                
                success, response = self.run_test(
                    "File Upload and Analysis",
                    "POST",
                    "chat/upload",
                    200,
                    data=data,
                    files=files
                )
                
                if success:
                    # Check if AI analyzed the file content
                    ai_message = response.get('assistant_message', {}).get('content', '')
                    if any(term in ai_message.lower() for term in ['blood pressure', 'hypertension', 'cholesterol']):
                        print("✅ AI successfully analyzed medical content")
                    else:
                        print("⚠️  AI may not have properly analyzed the medical content")
                
                return success
        
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_get_user_sessions(self):
        """Test getting user sessions"""
        return self.run_test(
            "Get User Sessions",
            "GET",
            f"chat/sessions/{self.user_id}",
            200
        )[0]

    def test_delete_session(self):
        """Test deleting a session"""
        if not self.session_id:
            print("❌ No session ID available for testing")
            return False
        
        return self.run_test(
            "Delete Session",
            "DELETE",
            f"chat/session/{self.session_id}",
            200
        )[0]

    def test_ai_integration(self):
        """Test AI integration with medical context"""
        # Create a new session for AI testing
        success, response = self.run_test(
            "Create Session for AI Test",
            "POST",
            "chat/session",
            200,
            data={
                "user_id": f"{self.user_id}_ai_test",
                "language": "spanish"  # Test multilingual support
            }
        )
        
        if not success:
            return False
        
        ai_session_id = response['id']
        
        # Test AI response in Spanish
        success, response = self.run_test(
            "AI Response in Spanish",
            "POST",
            "chat/message",
            200,
            data={
                "session_id": ai_session_id,
                "message": "¿Qué significa tener diabetes tipo 2?",
                "language": "spanish"
            }
        )
        
        if success:
            ai_message = response.get('assistant_message', {}).get('content', '')
            # Check if response is in Spanish and contains medical terms
            spanish_indicators = ['diabetes', 'tipo 2', 'médico', 'salud', 'tratamiento']
            if any(term in ai_message.lower() for term in spanish_indicators):
                print("✅ AI responded appropriately in Spanish")
            else:
                print("⚠️  AI response may not be in Spanish or lack medical context")
        
        # Clean up AI test session
        self.run_test(
            "Delete AI Test Session",
            "DELETE",
            f"chat/session/{ai_session_id}",
            200
        )
        
        return success

def main():
    print("🏥 Starting MedIntel AI Health Assistant API Tests")
    print("=" * 60)
    
    tester = MedIntelAPITester()
    
    # Run all tests in sequence
    test_results = []
    
    # Basic API tests
    test_results.append(("Health Check", tester.test_health_check()))
    test_results.append(("API Root", tester.test_api_root()))
    
    # Session management tests
    test_results.append(("Create Session", tester.test_create_session()))
    test_results.append(("Get Session", tester.test_get_session()))
    
    # Messaging tests
    test_results.append(("Send Message", tester.test_send_message()))
    test_results.append(("Get Messages", tester.test_get_messages()))
    
    # File upload test
    test_results.append(("File Upload", tester.test_file_upload()))
    
    # User sessions test
    test_results.append(("Get User Sessions", tester.test_get_user_sessions()))
    
    # AI integration test
    test_results.append(("AI Integration", tester.test_ai_integration()))
    
    # Cleanup test
    test_results.append(("Delete Session", tester.test_delete_session()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"\nOverall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the backend implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())