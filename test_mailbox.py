import os
import shutil
import json
import pytest
from fastapi.testclient import TestClient

# Adjust the import path if your main app is structured differently
# This assumes main.py (containing app = FastAPI()) and mailbox_router.py are in the same directory or accessible
from main import app 
from mailbox_router import (
    API_KEY, 
    DATA_DIR, 
    MAILBOXES_DIR, 
    AGENTS_FILE_PATH,
    _load_agent_names,
    _load_all_mailboxes_from_disk,
    agent_mailboxes,
    registered_agents
)

# Use TestClient for making requests to the FastAPI app
client = TestClient(app)

# Constants for testing
TEST_API_KEY = API_KEY # Use the same API key as the app for valid requests
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": TEST_API_KEY
}

# Helper functions to read data files directly
def load_agent_mailbox_file(agent_name):
    path = os.path.join(MAILBOXES_DIR, f"{agent_name}.json")
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None # Or raise error, depending on test needs
    return None

def load_agents_file():
    if os.path.exists(AGENTS_FILE_PATH):
        try:
            with open(AGENTS_FILE_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return [] # Or raise error
    return []

@pytest.fixture(autouse=True)
def cleanup_data_dir():
    """
    Fixture to clean up and reinitialize the data directory and in-memory state before each test.
    `autouse=True` makes it apply to all test methods automatically.
    """
    # --- Teardown phase (runs after each test) ---
    yield # Test runs here

    # --- Setup phase for the NEXT test (or cleanup after the current one) ---
    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR, ignore_errors=True)
    
    os.makedirs(MAILBOXES_DIR, exist_ok=True)
    
    # Clear global in-memory states in mailbox_router
    agent_mailboxes.clear()
    registered_agents.clear()
    
    # Reload state from disk (simulating app startup)
    _load_agent_names() # Loads from AGENTS_FILE_PATH if it exists
    _load_all_mailboxes_from_disk() # Loads from MAILBOXES_DIR


class TestAgentCreation:
    def test_add_agent_success(self):
        agent_name = "test_agent_add"
        response = client.post("/api/mailbox/agents/add", headers=HEADERS, json={"agent_name": agent_name})
        
        assert response.status_code == 200
        assert response.json()["status"] == f"Agent {agent_name} added successfully"

        # Verify file system
        agents_list = load_agents_file()
        assert agent_name in agents_list
        
        mailbox_data = load_agent_mailbox_file(agent_name)
        assert mailbox_data == {"max_key": 0, "messages": {}}

        # Verify in-memory state (after re-init by fixture, these should reflect the files)
        assert agent_name in registered_agents
        assert agent_name in agent_mailboxes
        assert agent_mailboxes[agent_name] == {"max_key": 0, "messages": {}}

    def test_add_agent_already_exists_in_registered_agents(self):
        agent_name = "existing_agent_reg"
        
        # Initial creation
        client.post("/api/mailbox/agents/add", headers=HEADERS, json={"agent_name": agent_name})
        
        # Attempt to add again
        response = client.post("/api/mailbox/agents/add", headers=HEADERS, json={"agent_name": agent_name})
        
        assert response.status_code == 409 # Conflict
        assert f"Agent '{agent_name}' already exists" in response.json()["detail"]
        
        # Verify files are not negatively altered (still one agent, one mailbox)
        agents_list = load_agents_file()
        assert agents_list.count(agent_name) == 1
        assert load_agent_mailbox_file(agent_name) is not None


    def test_add_agent_already_exists_as_mailbox_file(self):
        agent_name = "existing_agent_file"

        # Manually create a mailbox file to simulate pre-existence without being in agents.json yet
        # (This scenario might be less common with current logic but tests robustness)
        os.makedirs(MAILBOXES_DIR, exist_ok=True) # Ensure dir exists
        with open(os.path.join(MAILBOXES_DIR, f"{agent_name}.json"), 'w') as f:
            json.dump({"max_key": 0, "messages": {}}, f)
        
        # If the agent isn't in registered_agents yet, _load_all_mailboxes_from_disk would load it.
        # To make the test more specific for the endpoint's check, clear registered_agents
        # This simulates a state where the file exists but the agent isn't "formally" registered.
        registered_agents.clear() 
        # mailbox_router._load_all_mailboxes_from_disk() # this would load it into agent_mailboxes
        # The add_agent endpoint checks os.path.exists(_get_agent_mailbox_path(agent_name))

        response = client.post("/api/mailbox/agents/add", headers=HEADERS, json={"agent_name": agent_name})
        
        assert response.status_code == 409
        assert f"Agent '{agent_name}' already exists" in response.json()["detail"]


class TestMessageOperations:
    def test_send_message_new_recipient(self):
        sender_agent = "sender1"
        recipient_agent = "recipient1"
        message_content = "Hello Recipient1!"

        # Add sender explicitly to simplify test focus on recipient creation
        client.post("/api/mailbox/agents/add", headers=HEADERS, json={"agent_name": sender_agent})

        response = client.post(
            "/api/mailbox/send",
            headers=HEADERS,
            json={"message": message_content, "sender": sender_agent, "recipient": recipient_agent}
        )
        assert response.status_code == 200
        message_id = response.json()["message_id"]
        assert message_id == "msg1"

        # Verify recipient's mailbox file
        recipient_mailbox = load_agent_mailbox_file(recipient_agent)
        assert recipient_mailbox is not None
        assert recipient_mailbox["max_key"] == 1
        assert message_id in recipient_mailbox["messages"]
        assert recipient_mailbox["messages"][message_id]["message"] == message_content
        assert recipient_mailbox["messages"][message_id]["sender"] == sender_agent

        # Verify recipient is in agents.json
        agents_list = load_agents_file()
        assert recipient_agent in agents_list

        # Verify in-memory state
        assert recipient_agent in registered_agents
        assert recipient_agent in agent_mailboxes

    def test_send_message_existing_recipient(self):
        sender_agent = "sender2"
        recipient_agent = "recipient2"
        
        # Pre-register recipient
        client.post("/api/mailbox/agents/add", headers=HEADERS, json={"agent_name": recipient_agent})
        # Pre-register sender
        client.post("/api/mailbox/agents/add", headers=HEADERS, json={"agent_name": sender_agent})


        message1_content = "First message"
        response1 = client.post("/api/mailbox/send", headers=HEADERS, json={"message": message1_content, "sender": sender_agent, "recipient": recipient_agent})
        assert response1.status_code == 200
        msg1_id = response1.json()["message_id"]

        message2_content = "Second message"
        response2 = client.post("/api/mailbox/send", headers=HEADERS, json={"message": message2_content, "sender": sender_agent, "recipient": recipient_agent})
        assert response2.status_code == 200
        msg2_id = response2.json()["message_id"]

        recipient_mailbox = load_agent_mailbox_file(recipient_agent)
        assert recipient_mailbox["max_key"] == 2
        assert msg1_id in recipient_mailbox["messages"]
        assert msg2_id in recipient_mailbox["messages"]
        assert recipient_mailbox["messages"][msg2_id]["message"] == message2_content

    def test_get_messages_for_new_agent_implicitly_creates_mailbox(self):
        agent_name = "new_agent_get"
        response = client.get(f"/api/mailbox/messages/{agent_name}", headers=HEADERS)
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == agent_name
        assert data["messages"] == {}
        assert data["count"] == 0
        assert data["status"] == "No messages found"

        # Verify mailbox file and agents.json were created
        mailbox_data = load_agent_mailbox_file(agent_name)
        assert mailbox_data == {"max_key": 0, "messages": {}}
        
        agents_list = load_agents_file()
        assert agent_name in agents_list

        # Verify in-memory state
        assert agent_name in registered_agents
        assert agent_name in agent_mailboxes

    def test_get_messages_existing_agent(self):
        agent_name = "existing_agent_get"
        message_content = "Test content for get"
        
        # Send a message to create and populate the mailbox
        client.post("/api/mailbox/send", headers=HEADERS, json={"message": message_content, "sender": "another_agent", "recipient": agent_name})
        
        response = client.get(f"/api/mailbox/messages/{agent_name}", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == agent_name
        assert data["count"] == 1
        assert "msg1" in data["messages"]
        assert data["messages"]["msg1"]["message"] == message_content

    def test_delete_message(self):
        agent_name = "agent_del_msg"
        
        # Send two messages
        client.post("/api/mailbox/send", headers=HEADERS, json={"message": "msg to delete", "sender": "s", "recipient": agent_name})
        client.post("/api/mailbox/send", headers=HEADERS, json={"message": "msg to keep", "sender": "s", "recipient": agent_name})

        # Delete the first message (msg1)
        response = client.delete(f"/api/mailbox/messages/{agent_name}/msg1", headers=HEADERS)
        assert response.status_code == 200
        assert response.json()["status"] == "Message msg1 deleted successfully"

        mailbox_data = load_agent_mailbox_file(agent_name)
        assert "msg1" not in mailbox_data["messages"]
        assert "msg2" in mailbox_data["messages"] # msg2 should still be there
        assert mailbox_data["max_key"] == 2 # max_key is not decremented

        # Test deleting a non-existent message
        response_not_found = client.delete(f"/api/mailbox/messages/{agent_name}/msg_nonexistent", headers=HEADERS)
        assert response_not_found.status_code == 404

    def test_clear_mailbox(self):
        agent_name = "agent_clear_mail"
        client.post("/api/mailbox/send", headers=HEADERS, json={"message": "message1", "sender": "s", "recipient": agent_name})
        client.post("/api/mailbox/send", headers=HEADERS, json={"message": "message2", "sender": "s", "recipient": agent_name})

        response = client.delete(f"/api/mailbox/messages/{agent_name}", headers=HEADERS)
        assert response.status_code == 200
        assert response.json()["status"] == f"Mailbox for {agent_name} cleared successfully"

        mailbox_data = load_agent_mailbox_file(agent_name)
        assert mailbox_data["messages"] == {}
        assert mailbox_data["max_key"] == 2 # max_key is preserved

        # Verify agent still in agents.json
        agents_list = load_agents_file()
        assert agent_name in agents_list


class TestListAgents:
    def test_list_agents_empty(self):
        response = client.get("/api/mailbox/agents", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["agents"] == {}
        assert data["total_agents"] == 0

    def test_list_agents_with_data(self):
        agent1 = "listed_agent1"
        agent2 = "listed_agent2"

        # Create agent1 via send
        client.post("/api/mailbox/send", headers=HEADERS, json={"message": "hi", "sender": "s", "recipient": agent1})
        
        # Create agent2 via add
        client.post("/api/mailbox/agents/add", headers=HEADERS, json={"agent_name": agent2})
        client.post("/api/mailbox/send", headers=HEADERS, json={"message": "msg for agent2", "sender": "s", "recipient": agent2})


        response = client.get("/api/mailbox/agents", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_agents"] == 2
        assert agent1 in data["agents"]
        assert data["agents"][agent1]["message_count"] == 1
        assert data["agents"][agent1]["max_key"] == 1
        
        assert agent2 in data["agents"]
        assert data["agents"][agent2]["message_count"] == 1
        assert data["agents"][agent2]["max_key"] == 1
        
        # Verify against file system content (as a sanity check)
        # The cleanup fixture reloads globals from disk, so list_agents uses this fresh data
        assert len(os.listdir(MAILBOXES_DIR)) == 2 
        assert len(load_agents_file()) == 2


class TestAuthentication:
    def test_missing_api_key(self):
        response = client.get("/api/mailbox/agents", headers={"Content-Type": "application/json"})
        assert response.status_code == 401 # Should be 401 due to Depends(validate_api_key)
        # FastAPI's default for missing header in Depends is often a 422 if not handled,
        # but Header(None) makes it optional at function signature, then validate_api_key enforces it.
        # If validate_api_key raises HTTPException(401), this is correct.
        # If it was returning a 403, then the test would be specific to that.
        # The actual code raises 401 for invalid key, let's check behavior for missing.
        # The `validate_api_key` expects `x_api_key: str = Header(None)`.
        # If `X-API-Key` is missing, `x_api_key` will be `None`.
        # `None != API_KEY` will be true, so it raises HTTPException(401, detail="Invalid API key").
        assert "Invalid API key" in response.json()["detail"]


    def test_invalid_api_key(self):
        invalid_headers = HEADERS.copy()
        invalid_headers["X-API-Key"] = "wrong_key"
        response = client.get("/api/mailbox/agents", headers=invalid_headers)
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

# Example of how you might run specific tests with pytest:
# pytest test_mailbox.py -k TestAgentCreation
# pytest test_mailbox.py -k test_send_message_new_recipient

# To run all tests:
# pytest test_mailbox.py
