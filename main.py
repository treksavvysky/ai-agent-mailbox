# main.py - Your main FastAPI application
from fastapi import FastAPI
from mailbox_router import mailbox_router  # Import the router

# Create your main FastAPI app
app = FastAPI(title="AI Agent Communication System")

# Include the mailbox router
app.include_router(mailbox_router)

# Your other routes...
@app.get("/")
def root():
    return {"message": "AI Agent Communication System is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
