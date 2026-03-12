from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from pydantic_ai.messages import ModelResponse, ModelMessage
from src.rag_tool import get_agent

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
        message_history=chat_req.message_history
    )
    return result.response