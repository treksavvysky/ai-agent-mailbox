# AI Agent Mailbox System

A secure, FastAPI-based messaging system designed for inter-agent communication, allowing AI agents (like custom GPTs) to send, receive, and manage messages through a clean REST API interface.

## 🚀 Features

- **Agent-Specific Mailboxes**: Each AI agent has its own dedicated message storage
- **Secure API Access**: API key authentication for all endpoints
- **Message Management**: Send, retrieve, delete individual messages or clear entire mailboxes
- **Automatic Initialization**: Agent mailboxes are created automatically on first use
- **RESTful Interface**: Clean, intuitive API endpoints following REST conventions
- **Pydantic Validation**: Built-in request/response validation with proper error handling
- **OpenAPI Documentation**: Complete API specification for easy integration

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

## 🛠 Installation

### Prerequisites
- Python 3.7+
- FastAPI
- Uvicorn (for running the server)

### Install Dependencies

```bash
pip install fastapi uvicorn python-dotenv
```

### Project Structure

```
ai-agent-mailbox/
├── __init__.py
├── mailbox_router.py
├── main.py
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Quick Start

### 1. Set up your environment

Create a `.env` file:
```bash
MAILBOX_API_KEY=your-super-secret-api-key-here
```

### 2. Create your main application

```python
# main.py
from fastapi import FastAPI
from mailbox_router import mailbox_router

app = FastAPI(title="AI Agent Communication System")
app.include_router(mailbox_router)

@app.get("/")
def root():
    return {"message": "AI Agent Communication System is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. Run the server

```bash
python main.py
```

Your API will be available at `http://localhost:8000`

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/mailbox/send` | Send a message to a specific agent |
| `GET` | `/api/mailbox/messages/{agent_name}` | Retrieve all messages for an agent |
| `DELETE` | `/api/mailbox/messages/{agent_name}/{message_id}` | Delete a specific message |
| `DELETE` | `/api/mailbox/messages/{agent_name}` | Clear all messages for an agent |
| `GET` | `/api/mailbox/agents` | List all agents and their message statistics |

## 🔐 Authentication

All endpoints require an API key passed in the `X-API-Key` header:

```bash
X-API-Key: your-secret-api-key-here
```

## 💡 Usage Examples

### Send a Message

```python
import requests

headers = {
    "Content-Type": "application/json",
    "X-API-Key": "your-secret-api-key-here"
}

message_data = {
    "message": "Hello, this is a test message!",
    "sender": "GPT-Agent-1",
    "recipient": "GPT-Agent-2"
}

response = requests.post(
    "http://localhost:8000/api/mailbox/send",
    headers=headers,
    json=message_data
)

print(response.json())
# Output: {"status": "Message sent successfully", "message_id": "msg1"}
```

### Retrieve Messages

```python
agent_name = "GPT-Agent-2"
response = requests.get(
    f"http://localhost:8000/api/mailbox/messages/{agent_name}",
    headers=headers
)

print(response.json())
# Output: {
#   "agent": "GPT-Agent-2",
#   "messages": {
#     "msg1": {
#       "message": "Hello, this is a test message!",
#       "sender": "GPT-Agent-1",
#       "recipient": "GPT-Agent-2",
#       "timestamp": "2025-05-28 10:30:00"
#     }
#   },
#   "count": 1,
#   "status": "Messages retrieved successfully"
# }
```

### cURL Examples

**Send a message:**
```bash
curl -X POST "http://localhost:8000/api/mailbox/send" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-secret-api-key-here" \
     -d '{
       "message": "Hello from Agent1!",
       "sender": "Agent1",
       "recipient": "Agent2"
     }'
```

**Get messages:**
```bash
curl -X GET "http://localhost:8000/api/mailbox/messages/Agent2" \
     -H "X-API-Key: your-secret-api-key-here"
```

**List all agents:**
```bash
curl -X GET "http://localhost:8000/api/mailbox/agents" \
     -H "X-API-Key: your-secret-api-key-here"
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MAILBOX_API_KEY` | API key for authentication | `your-secret-api-key-here` |

### Message Structure

Messages are stored with the following fields:

```json
{
  "message": "The actual message content",
  "sender": "Name of the sending agent",
  "recipient": "Name of the receiving agent",
  "timestamp": "2025-05-28 10:30:00"
}
```

## 📚 API Documentation

### Interactive Documentation

Once your server is running, you can access:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### OpenAPI Specification

The complete OpenAPI 3.0.3 specification is available and can be used with any OpenAPI-compatible tools or AI agents that need to interact with the API.

## 🔧 Development

### Running in Development Mode

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testing the API

```python
# test_mailbox.py
import requests
import time

BASE_URL = "http://localhost:8000/api/mailbox"
API_KEY = "your-secret-api-key-here"
HEADERS = {"Content-Type": "application/json", "X-API-Key": API_KEY}

def test_workflow():
    # Send a message
    message_data = {
        "message": "Test message",
        "sender": "TestAgent1",
        "recipient": "TestAgent2"
    }
    
    response = requests.post(f"{BASE_URL}/send", headers=HEADERS, json=message_data)
    assert response.status_code == 200
    
    # Retrieve messages
    response = requests.get(f"{BASE_URL}/messages/TestAgent2", headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["count"] > 0
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    test_workflow()
```

## 🏗️ Production Considerations

### Security
- **Use strong API keys** in production environments
- **Implement rate limiting** to prevent abuse
- **Enable HTTPS** for encrypted communication
- **Monitor API access** for security auditing

### Storage
- Current implementation uses **in-memory storage**
- For production, consider implementing:
  - **Database storage** (PostgreSQL, MySQL)
  - **Redis** for high-performance caching
  - **Message persistence** and backup strategies

### Scalability
- **Horizontal scaling** with load balancers
- **Database optimization** for high message volumes
- **Caching strategies** for frequently accessed data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [API documentation](#api-documentation)
2. Review the [usage examples](#usage-examples)
3. Open an issue on GitHub

## 🎯 Use Cases

- **Multi-agent AI systems** coordination
- **Custom GPT communication** workflows
- **Automated task delegation** between AI agents
- **Message queuing** for asynchronous AI operations
- **Inter-service communication** in microservices architectures

---

**Happy messaging!** 🤖💬