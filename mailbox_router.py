from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
import os

# Pydantic models for request/response validation
class MessageRequest(BaseModel):
    message: str
    sender: Optional[str] = "Assistant"
    recipient: str  # The agent that should receive this message

class MessageResponse(BaseModel):
    status: str
    message_id: Optional[str] = None

# In-memory storage (consider using a database for production)
# Structure: {agent_name: {message_id: message_data, 'max_key': int}}
agent_mailboxes: Dict[str, Dict[str, Any]] = {}

# API key validation
API_KEY = os.getenv("MAILBOX_API_KEY", "your-secret-api-key-here")

def validate_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Create the router
mailbox_router = APIRouter(prefix="/api/mailbox", tags=["mailbox"])

def initialize_agent_mailbox(agent_name: str):
    """Initialize mailbox for a new agent if it doesn't exist"""
    if agent_name not in agent_mailboxes:
        agent_mailboxes[agent_name] = {"max_key": 0}

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
        
        # Create message data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        max_key = agent_mailboxes[message_data.recipient]["max_key"] + 1
        message_id = f"msg{max_key}"
        
        # Store the message
        agent_mailboxes[message_data.recipient][message_id] = {
            "message": message_data.message,
            "sender": message_data.sender,
            "recipient": message_data.recipient,
            "timestamp": timestamp
        }
        
        # Update max_key
        agent_mailboxes[message_data.recipient]["max_key"] = max_key
        
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
        # Initialize agent's mailbox if it doesn't exist
        initialize_agent_mailbox(agent_name)
        
        # Get all messages except the max_key
        messages = {k: v for k, v in agent_mailboxes[agent_name].items() if k != "max_key"}
        
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
        if agent_name not in agent_mailboxes:
            raise HTTPException(status_code=404, detail="Agent mailbox not found")
        
        if message_id not in agent_mailboxes[agent_name]:
            raise HTTPException(status_code=404, detail="Message not found")
        
        if message_id == "max_key":
            raise HTTPException(status_code=400, detail="Cannot delete system key")
        
        # Delete the message
        del agent_mailboxes[agent_name][message_id]
        
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
        if agent_name not in agent_mailboxes:
            raise HTTPException(status_code=404, detail="Agent mailbox not found")
        
        # Keep only the max_key, remove all messages
        max_key = agent_mailboxes[agent_name].get("max_key", 0)
        agent_mailboxes[agent_name] = {"max_key": max_key}
        
        return {"status": f"Mailbox for {agent_name} cleared successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear mailbox: {str(e)}")

@mailbox_router.get("/agents")
def list_agents(api_key: str = Depends(validate_api_key)):
    """
    List all agents that have mailboxes
    """
    try:
        agents_info = {}
        for agent_name, mailbox in agent_mailboxes.items():
            message_count = len([k for k in mailbox.keys() if k != "max_key"])
            agents_info[agent_name] = {
                "message_count": message_count,
                "max_key": mailbox.get("max_key", 0)
            }
        
        return {
            "agents": agents_info,
            "total_agents": len(agents_info),
            "status": "Agents listed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")
