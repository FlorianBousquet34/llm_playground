from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from pydantic_ai import UsageLimits
from pydantic_ai.messages import ModelResponse, ModelMessage
import uvicorn
from src.rag_tool import get_agent
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Input schema
class ChatRequest(BaseModel):
    user_query: str
    message_history: List[ModelMessage] = []

@app.post("/chat", response_model=ModelResponse)
def chat_endpoint(chat_req: ChatRequest):
    # Run the agent with the provided history
    result = get_agent().run_sync(
        user_prompt=chat_req.user_query,
        message_history=chat_req.message_history,
        usage_limits=UsageLimits(request_limit=5, tool_calls_limit=3)
    )
    return result.response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True 
    )