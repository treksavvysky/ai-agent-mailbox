from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
import os
import json

# Pydantic models for request/response validation
class MessageRequest(BaseModel):
    message: str
    sender: Optional[str] = "Assistant"
    recipient: str  # The agent that should receive this message

class MessageResponse(BaseModel):
    status: str
    message_id: Optional[str] = None

class AgentCreateRequest(BaseModel):
    agent_name: str

# Define base data directory and mailboxes directory
DATA_DIR = "data"
MAILBOXES_DIR = os.path.join(DATA_DIR, "mailboxes")
AGENTS_FILE_PATH = os.path.join(DATA_DIR, "agents.json")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MAILBOXES_DIR, exist_ok=True)

# Global set to store registered agent names
registered_agents: set[str] = set()

def _load_agent_names():
    """Loads agent names from AGENTS_FILE_PATH into the registered_agents set."""
    global registered_agents
    if os.path.exists(AGENTS_FILE_PATH):
        try:
            with open(AGENTS_FILE_PATH, 'r') as f:
                agents_list = json.load(f)
                if isinstance(agents_list, list):
                    registered_agents = set(agents_list)
                else:
                    print(f"Error: {AGENTS_FILE_PATH} does not contain a valid list.") # Replace with proper logging
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading agent names from {AGENTS_FILE_PATH}: {e}") # Replace with proper logging
    # If file not found, registered_agents remains empty, which is fine for the first run.

_load_agent_names() # Load agent names on startup

def _save_agent_names():
    """Saves the registered_agents set to AGENTS_FILE_PATH."""
    global registered_agents
    try:
        with open(AGENTS_FILE_PATH, 'w') as f:
            json.dump(list(registered_agents), f, indent=4)
    except IOError as e:
        print(f"Error saving agent names to {AGENTS_FILE_PATH}: {e}") # Replace with proper logging


def _get_agent_mailbox_path(agent_name: str) -> str:
    """Returns the path to the agent's mailbox JSON file."""
    return os.path.join(MAILBOXES_DIR, f"{agent_name}.json")

# Load mailboxes from files on startup
agent_mailboxes: Dict[str, Dict[str, Any]] = {}

def _load_all_mailboxes_from_disk():
    """Clears and reloads all agent mailboxes from disk."""
    global agent_mailboxes
    agent_mailboxes.clear()
    for filename in os.listdir(MAILBOXES_DIR):
        if filename.endswith(".json"):
            agent_name = filename[:-5]
            filepath = _get_agent_mailbox_path(agent_name)
            try:
                with open(filepath, 'r') as f:
                    agent_mailboxes[agent_name] = json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading mailbox for {agent_name}: {e}") # Replace with proper logging

_load_all_mailboxes_from_disk() # Initial load on startup

# Structure: {agent_name: {"max_key": 0, "messages": {}}}
# agent_mailboxes is now initialized above by loading from files

# API key validation
API_KEY = os.getenv("MAILBOX_API_KEY", "your-secret-api-key-here")

def validate_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Create the router
mailbox_router = APIRouter(prefix="/api/mailbox", tags=["mailbox"])

def _save_mailbox(agent_name: str):
    """Saves the agent's mailbox to their JSON file."""
    filepath = _get_agent_mailbox_path(agent_name)
    try:
        with open(filepath, 'w') as f:
            json.dump(agent_mailboxes[agent_name], f, indent=4)
    except IOError as e:
        print(f"Error saving mailbox for {agent_name}: {e}") # Replace with proper logging


def initialize_agent_mailbox(agent_name: str):
    """Initialize mailbox for a new agent if it doesn't exist or load it."""
    global registered_agents
    mailbox_initialized_or_loaded = False
    if agent_name not in agent_mailboxes:
        filepath = _get_agent_mailbox_path(agent_name)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    agent_mailboxes[agent_name] = json.load(f)
                mailbox_initialized_or_loaded = True
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading mailbox for {agent_name}: {e}") # Replace with proper logging
                # Initialize fresh if loading fails
                agent_mailboxes[agent_name] = {"max_key": 0, "messages": {}}
                _save_mailbox(agent_name)
                mailbox_initialized_or_loaded = True # Still counts as initialized
        else:
            agent_mailboxes[agent_name] = {"max_key": 0, "messages": {}}
            _save_mailbox(agent_name)
            mailbox_initialized_or_loaded = True
    else: # Agent already in agent_mailboxes (memory), so it's considered initialized
        mailbox_initialized_or_loaded = True

    if mailbox_initialized_or_loaded and agent_name not in registered_agents:
        registered_agents.add(agent_name)
        _save_agent_names()


@mailbox_router.post("/send", response_model=MessageResponse)
def send_message(
    message_data: MessageRequest,
    api_key: str = Depends(validate_api_key)
):
    """
    Send a message to a specific agent's mailbox
    """
    try:
        # Initialize recipient's mailbox if needed
        initialize_agent_mailbox(message_data.recipient)
        
        recipient_mailbox = agent_mailboxes[message_data.recipient]
        
        # Create message data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        recipient_mailbox["max_key"] += 1
        message_id = f"msg{recipient_mailbox['max_key']}"
        
        # Store the message
        recipient_mailbox["messages"][message_id] = {
            "message": message_data.message,
            "sender": message_data.sender,
            "recipient": message_data.recipient,
            "timestamp": timestamp
        }
        
        _save_mailbox(message_data.recipient)
        
        return MessageResponse(
            status="Message sent successfully",
            message_id=message_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@mailbox_router.get("/messages/{agent_name}")
def get_messages(
    agent_name: str,
    api_key: str = Depends(validate_api_key)
):
    """
    Retrieve all messages for a specific agent
    """
    try:
        # Initialize agent's mailbox if it doesn't exist (e.g. if file was deleted)
        initialize_agent_mailbox(agent_name)
        
        messages = agent_mailboxes[agent_name].get("messages", {})
        
        if not messages:
            return {
                "agent": agent_name,
                "messages": {},
                "count": 0,
                "status": "No messages found"
            }
        
        return {
            "agent": agent_name,
            "messages": messages,
            "count": len(messages),
            "status": "Messages retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve messages: {str(e)}")

@mailbox_router.delete("/messages/{agent_name}/{message_id}")
def delete_message(
    agent_name: str,
    message_id: str,
    api_key: str = Depends(validate_api_key)
):
    """
    Delete a specific message from an agent's mailbox
    """
    try:
        initialize_agent_mailbox(agent_name) # Ensure mailbox is loaded

        if agent_name not in agent_mailboxes: # Should not happen if initialize works
            raise HTTPException(status_code=404, detail="Agent mailbox not found")
        
        if message_id not in agent_mailboxes[agent_name].get("messages", {}):
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Delete the message
        del agent_mailboxes[agent_name]["messages"][message_id]
        _save_mailbox(agent_name)
        
        return {"status": f"Message {message_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete message: {str(e)}")

@mailbox_router.delete("/messages/{agent_name}")
def clear_mailbox(
    agent_name: str,
    api_key: str = Depends(validate_api_key)
):
    """
    Clear all messages from an agent's mailbox
    """
    try:
        initialize_agent_mailbox(agent_name) # Ensure mailbox is loaded

        if agent_name not in agent_mailboxes: # Should not happen
            raise HTTPException(status_code=404, detail="Agent mailbox not found")
        
        # Clear messages, keep max_key
        agent_mailboxes[agent_name]["messages"] = {}
        _save_mailbox(agent_name)
        
        return {"status": f"Mailbox for {agent_name} cleared successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear mailbox: {str(e)}")

@mailbox_router.get("/agents")
def list_agents(api_key: str = Depends(validate_api_key)):
    """
    List all agents that have mailboxes
    """
    try:
        # agent_mailboxes is already populated from files at startup
        agents_info = {}
        for agent_name, mailbox_content in agent_mailboxes.items():
            agents_info[agent_name] = {
                "message_count": len(mailbox_content.get("messages", {})),
                "max_key": mailbox_content.get("max_key", 0)
            }
        
        return {
            "agents": agents_info,
            "total_agents": len(agents_info),
            "status": "Agents listed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@mailbox_router.post("/agents/add", response_model=MessageResponse)
async def add_agent(agent_data: AgentCreateRequest, api_key: str = Depends(validate_api_key)):
    """
    Register a new agent and initialize their mailbox.
    """
    agent_name = agent_data.agent_name

    # Check if agent already exists
    if agent_name in registered_agents or os.path.exists(_get_agent_mailbox_path(agent_name)):
        raise HTTPException(status_code=409, detail=f"Agent '{agent_name}' already exists.")

    try:
        # Register new agent
        registered_agents.add(agent_name)
        _save_agent_names() # Persist the updated set to data/agents.json

        # Initialize mailbox (creates file and updates in-memory dicts)
        # initialize_agent_mailbox already handles adding to registered_agents and saving if the agent wasn't known,
        # but here we call it primarily to ensure the mailbox file itself is created and agent_mailboxes is populated.
        # The previous add/save to registered_agents ensures it's known to that list first.
        initialize_agent_mailbox(agent_name)
        
        # Ensure the mailbox was actually created by initialize_agent_mailbox
        if not os.path.exists(_get_agent_mailbox_path(agent_name)):
             # This case should ideally not be reached if initialize_agent_mailbox works as expected
            raise HTTPException(status_code=500, detail=f"Failed to create mailbox file for agent '{agent_name}'.")

        return MessageResponse(status=f"Agent {agent_name} added successfully")

    except HTTPException: # Re-raise if it's an HTTPException (like the 409 above)
        raise
    except Exception as e:
        # Attempt to rollback adding agent name if other errors occur
        if agent_name in registered_agents:
            registered_agents.remove(agent_name)
            _save_agent_names()
        raise HTTPException(status_code=500, detail=f"Failed to add agent '{agent_name}': {str(e)}")
