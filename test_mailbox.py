# test_mailbox.py - Test script for the AI Agent Mailbox System
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/mailbox"
API_KEY = "your-secret-api-key-here"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def test_send_message():
    """Test sending a message"""
    print("🧪 Testing: Send Message")
    
    message_data = {
        "message": "Hello, this is a test message!",
        "sender": "TestAgent1",
        "recipient": "TestAgent2"
    }
    
    response = requests.post(f"{BASE_URL}/send", headers=HEADERS, json=message_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Message sent successfully: {result['message_id']}")
        return result['message_id']
    else:
        print(f"❌ Failed to send message: {response.status_code} - {response.text}")
        return None

def test_get_messages(agent_name):
    """Test retrieving messages for an agent"""
    print(f"🧪 Testing: Get Messages for {agent_name}")
    
    response = requests.get(f"{BASE_URL}/messages/{agent_name}", headers=HEADERS)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Retrieved {result['count']} messages for {agent_name}")
        return result
    else:
        print(f"❌ Failed to get messages: {response.status_code} - {response.text}")
        return None

def test_list_agents():
    """Test listing all agents"""
    print("🧪 Testing: List Agents")
    
    response = requests.get(f"{BASE_URL}/agents", headers=HEADERS)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Found {result['total_agents']} agents")
        for agent, info in result['agents'].items():
            print(f"   - {agent}: {info['message_count']} messages")
        return result
    else:
        print(f"❌ Failed to list agents: {response.status_code} - {response.text}")
        return None

def test_delete_message(agent_name, message_id):
    """Test deleting a specific message"""
    print(f"🧪 Testing: Delete Message {message_id} for {agent_name}")
    
    response = requests.delete(f"{BASE_URL}/messages/{agent_name}/{message_id}", headers=HEADERS)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result['status']}")
        return True
    else:
        print(f"❌ Failed to delete message: {response.status_code} - {response.text}")
        return False

def test_clear_mailbox(agent_name):
    """Test clearing all messages for an agent"""
    print(f"🧪 Testing: Clear Mailbox for {agent_name}")
    
    response = requests.delete(f"{BASE_URL}/messages/{agent_name}", headers=HEADERS)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result['status']}")
        return True
    else:
        print(f"❌ Failed to clear mailbox: {response.status_code} - {response.text}")
        return False

def test_workflow():
    """Run a complete test workflow"""
    print("🚀 Starting AI Agent Mailbox Test Workflow")
    print("=" * 50)
    
    # Test 1: Send multiple messages
    message_ids = []
    for i in range(3):
        message_data = {
            "message": f"Test message {i+1} from Agent1",
            "sender": "TestAgent1",
            "recipient": "TestAgent2"
        }
        response = requests.post(f"{BASE_URL}/send", headers=HEADERS, json=message_data)
        if response.status_code == 200:
            message_ids.append(response.json()['message_id'])
    
    # Send a message to a different agent
    message_data = {
        "message": "Hello from Agent3!",
        "sender": "TestAgent3",
        "recipient": "TestAgent4"
    }
    requests.post(f"{BASE_URL}/send", headers=HEADERS, json=message_data)
    
    print(f"📨 Sent {len(message_ids) + 1} test messages")
    
    # Test 2: Retrieve messages
    messages = test_get_messages("TestAgent2")
    if messages and messages['count'] > 0:
        print("📬 Sample message:")
        first_msg_id = list(messages['messages'].keys())[0]
        first_msg = messages['messages'][first_msg_id]
        print(f"   ID: {first_msg_id}")
        print(f"   From: {first_msg['sender']}")
        print(f"   Content: {first_msg['message']}")
        print(f"   Time: {first_msg['timestamp']}")
    
    # Test 3: List all agents
    test_list_agents()
    
    # Test 4: Delete a specific message
    if message_ids:
        test_delete_message("TestAgent2", message_ids[0])
    
    # Test 5: Verify deletion
    messages_after_delete = test_get_messages("TestAgent2")
    if messages_after_delete:
        print(f"📬 Messages after deletion: {messages_after_delete['count']}")
    
    # Test 6: Clear entire mailbox
    test_clear_mailbox("TestAgent2")
    
    # Test 7: Verify mailbox is empty
    messages_after_clear = test_get_messages("TestAgent2")
    if messages_after_clear:
        print(f"📬 Messages after clearing: {messages_after_clear['count']}")
    
    print("=" * 50)
    print("✅ Test workflow completed!")

def test_authentication():
    """Test API key authentication"""
    print("🧪 Testing: Authentication")
    
    # Test with invalid API key
    invalid_headers = {
        "Content-Type": "application/json",
        "X-API-Key": "invalid-key"
    }
    
    response = requests.get(f"{BASE_URL}/agents", headers=invalid_headers)
    
    if response.status_code == 401:
        print("✅ Authentication correctly rejected invalid API key")
    else:
        print(f"❌ Authentication test failed: {response.status_code}")
    
    # Test with missing API key
    no_key_headers = {"Content-Type": "application/json"}
    response = requests.get(f"{BASE_URL}/agents", headers=no_key_headers)
    
    if response.status_code == 401:
        print("✅ Authentication correctly rejected missing API key")
    else:
        print(f"❌ Authentication test failed: {response.status_code}")

if __name__ == "__main__":
    print("🤖 AI Agent Mailbox System - Test Suite")
    print("Make sure your server is running on http://localhost:8000")
    print("Update the API_KEY variable if you've changed the default")
    print()
    
    try:
        # Test authentication first
        test_authentication()
        print()
        
        # Run the main workflow
        test_workflow()
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running on http://localhost:8000")
        print("Run: python main.py")
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
