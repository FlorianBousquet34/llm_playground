import uuid

from fastapi import FastAPI
from ollama import Message
from pydantic import BaseModel
from typing import List
from pydantic_ai import UsageLimits
from pydantic_ai.messages import ModelResponse, ModelMessage
import uvicorn
from src.llm_client import OllamaLLMClient
from src.rag_tool import get_agent
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Input schema
class ChatRequest(BaseModel):
    user_query: str
    message_history: List[ModelMessage] = []
    
class ChatResponse(BaseModel):
    history: List[Message] = []
    response: ModelResponse

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(chat_req: ChatRequest):
    # Run the agent with the provided history
    req_id = str(uuid.uuid4())
    agent = get_agent()
    llm_client: OllamaLLMClient = agent.model.client
    llm_client.history[req_id] = []
    result = agent.run_sync(
        user_prompt=chat_req.user_query,
        message_history=chat_req.message_history,
        usage_limits=UsageLimits(request_limit=5, tool_calls_limit=3),
        metadata={"req_id": req_id}
    )
    history = llm_client.history.pop(req_id, None)
    return ChatResponse(history=history, response=result.response)

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