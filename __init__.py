"""
AI Agent Mailbox System

A FastAPI-based messaging system designed for inter-agent communication, allowing AI agents
to send, receive, and manage messages through a secure REST API interface.

Features:
---------
- **Agent-Specific Mailboxes**: Each AI agent has its own dedicated message storage
- **Secure API Access**: API key authentication via headers for all endpoints
- **Message Management**: Send, retrieve, delete individual messages or clear entire mailboxes
- **Automatic Initialization**: Agent mailboxes are created automatically on first use
- **RESTful Interface**: Clean, intuitive API endpoints following REST conventions
- **Pydantic Validation**: Request/response validation with proper error handling

Endpoints:
----------
- POST /api/mailbox/send - Send a message to a specific agent
- GET /api/mailbox/messages/{agent_name} - Retrieve all messages for an agent
- DELETE /api/mailbox/messages/{agent_name}/{message_id} - Delete a specific message
- DELETE /api/mailbox/messages/{agent_name} - Clear all messages for an agent
- GET /api/mailbox/agents - List all agents and their message statistics

Authentication:
---------------
All endpoints require an API key passed in the 'X-API-Key' header. Configure the key
using the MAILBOX_API_KEY environment variable or update the default in the router.

Usage Example:
--------------
```python
from fastapi import FastAPI
from mailbox import mailbox_router

app = FastAPI()
app.include_router(mailbox_router)

# Send a message via API:
# POST /api/mailbox/send
# Headers: {"X-API-Key": "your-api-key"}
# Body: {"message": "Hello!", "sender": "Agent1", "recipient": "Agent2"}
```

Message Structure:
------------------
Messages are stored with the following fields:
- message: The actual message content
- sender: Name of the sending agent (defaults to "Assistant")
- recipient: Name of the receiving agent (required)
- timestamp: Auto-generated timestamp in YYYY-MM-DD HH:MM:SS format

Storage:
--------
Currently uses in-memory storage suitable for development and testing.
For production use, consider implementing persistent storage (database, Redis, etc.).

Security Notes:
---------------
- Always use strong, unique API keys in production
- Consider implementing rate limiting for production deployments
- Monitor and log API access for security auditing
"""