# usage_examples.py - Practical examples for using the AI Agent Mailbox System
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api/mailbox"
API_KEY = "your-secret-api-key-here"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def example_1_basic_messaging():
    """Example 1: Basic agent-to-agent messaging"""
    print("📝 Example 1: Basic Messaging")
    print("-" * 30)
    
    # Agent1 sends a message to Agent2
    message_data = {
        "message": "Hello Agent2! Can you process the data from yesterday?",
        "sender": "DataCollectorAgent",
        "recipient": "DataProcessorAgent"
    }
    
    response = requests.post(f"{BASE_URL}/send", headers=HEADERS, json=message_data)
    print(f"Message sent: {response.json()}")
    
    # Agent2 checks for messages
    response = requests.get(f"{BASE_URL}/messages/DataProcessorAgent", headers=HEADERS)
    messages = response.json()
    print(f"Messages for DataProcessorAgent: {messages['count']} messages")
    
    for msg_id, msg in messages['messages'].items():
        print(f"  {msg_id}: {msg['message'][:50]}...")

def example_2_task_coordination():
    """Example 2: Multi-agent task coordination"""
    print("\n📝 Example 2: Task Coordination")
    print("-" * 30)
    
    # Coordinator assigns tasks
    tasks = [
        {"agent": "WebScraperAgent", "task": "Scrape product prices from 5 websites"},
        {"agent": "DataAnalyzerAgent", "task": "Analyze price trends from scraped data"},
        {"agent": "ReportGeneratorAgent", "task": "Generate weekly price report"}
    ]
    
    for task in tasks:
        message_data = {
            "message": f"Task Assignment: {task['task']}",
            "sender": "CoordinatorAgent",
            "recipient": task['agent']
        }
        
        response = requests.post(f"{BASE_URL}/send", headers=HEADERS, json=message_data)
        print(f"Task assigned to {task['agent']}")
    
    # Check all active agents
    response = requests.get(f"{BASE_URL}/agents", headers=HEADERS)
    agents = response.json()
    print(f"\nActive agents: {list(agents['agents'].keys())}")

def example_3_status_updates():
    """Example 3: Status updates and notifications"""
    print("\n📝 Example 3: Status Updates")
    print("-" * 30)
    
    # Agents report their status back to coordinator
    status_updates = [
        {"from": "WebScraperAgent", "status": "Scraping completed - 500 products processed"},
        {"from": "DataAnalyzerAgent", "status": "Analysis in progress - 60% complete"},
        {"from": "ReportGeneratorAgent", "status": "Waiting for analysis data"}
    ]
    
    for update in status_updates:
        message_data = {
            "message": f"Status Update: {update['status']}",
            "sender": update['from'],
            "recipient": "CoordinatorAgent"
        }
        
        requests.post(f"{BASE_URL}/send", headers=HEADERS, json=message_data)
    
    # Coordinator checks all status updates
    response = requests.get(f"{BASE_URL}/messages/CoordinatorAgent", headers=HEADERS)
    messages = response.json()
    
    print("Status updates received:")
    for msg_id, msg in messages['messages'].items():
        print(f"  From {msg['sender']}: {msg['message']}")

def example_4_error_handling():
    """Example 4: Error handling and notifications"""
    print("\n📝 Example 4: Error Handling")
    print("-" * 30)
    
    # Simulate an agent encountering an error
    error_message = {
        "message": "ERROR: Unable to connect to data source. Retrying in 5 minutes.",
        "sender": "DatabaseAgent",
        "recipient": "MonitoringAgent"
    }
    
    response = requests.post(f"{BASE_URL}/send", headers=HEADERS, json=error_message)
    print("Error notification sent to monitoring agent")
    
    # Monitoring agent checks for errors
    response = requests.get(f"{BASE_URL}/messages/MonitoringAgent", headers=HEADERS)
    messages = response.json()
    
    error_messages = []
    for msg_id, msg in messages['messages'].items():
        if "ERROR" in msg['message']:
            error_messages.append(msg)
    
    print(f"Found {len(error_messages)} error notifications")

def example_5_cleanup_operations():
    """Example 5: Message cleanup and maintenance"""
    print("\n📝 Example 5: Cleanup Operations")
    print("-" * 30)
    
    # List all agents and their message counts
    response = requests.get(f"{BASE_URL}/agents", headers=HEADERS)
    agents = response.json()
    
    print("Current mailbox status:")
    for agent, info in agents['agents'].items():
        print(f"  {agent}: {info['message_count']} messages")
    
    # Clean up processed messages (example: clear CoordinatorAgent mailbox)
    if 'CoordinatorAgent' in agents['agents']:
        response = requests.delete(f"{BASE_URL}/messages/CoordinatorAgent", headers=HEADERS)
        print("\nCleared CoordinatorAgent mailbox")
    
    # Alternatively, delete specific messages
    # response = requests.delete(f"{BASE_URL}/messages/AgentName/msg1", headers=HEADERS)

def run_all_examples():
    """Run all examples in sequence"""
    print("🤖 AI Agent Mailbox System - Usage Examples")
    print("=" * 50)
    
    try:
        example_1_basic_messaging()
        example_2_task_coordination()
        example_3_status_updates()
        example_4_error_handling()
        example_5_cleanup_operations()
        
        print("\n" + "=" * 50)
        print("✅ All examples completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Example failed with error: {str(e)}")

if __name__ == "__main__":
    run_all_examples()
