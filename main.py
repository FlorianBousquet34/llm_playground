import json
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI
from ollama import Message
from pydantic import BaseModel
from typing import List
from pydantic_ai import UsageLimits
from pydantic_ai.messages import ModelResponse, ModelMessage
import uvicorn
from dynamic_injection_batch import INDEXATION_CONFIGURATION_FILE
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

class IndexedFolder(BaseModel):
    path: str
    index_type: str

class SettingsModel(BaseModel):
    system_prompt: str
    model_name: str
    indexed_folders: list[IndexedFolder]
    indexation_frequency: int
    
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

@app.post("/settings")
def update_settings(update_settings: SettingsModel):
    agent = get_agent()
    llm_client: OllamaLLMClient = agent.model.client
    llm_client.system_prompt = update_settings.system_prompt
    llm_client.model_name = update_settings.model_name
    with open(INDEXATION_CONFIGURATION_FILE, "r") as f:
        indexation_conf_data = json.loads(f.read())
        indexation_conf_data["documentation_folders"]["text"]=[fld.path for fld in filter(lambda x: x.index_type == "documentation", update_settings.indexed_folders)]
        indexation_conf_data["code_folders"]["javascript"]=[fld.path for fld in filter(lambda x: x.index_type == "code_javascript", update_settings.indexed_folders)]
        indexation_conf_data["index_frequency"]=update_settings.indexation_frequency
    with open(INDEXATION_CONFIGURATION_FILE, "w") as f:
        f.write(json.dumps(indexation_conf_data))
        
@app.get("/settings", response_model=SettingsModel)
def get_settings():
    agent = get_agent()
    llm_client: OllamaLLMClient = agent.model.client
    with open(INDEXATION_CONFIGURATION_FILE, "r") as f:
        indexation_conf_data = json.loads(f.read())
    doc_folder_to_index = indexation_conf_data["documentation_folders"]["text"]
    js_code_folder_to_index = indexation_conf_data["code_folders"]["javascript"]
    index_frequency = indexation_conf_data["index_frequency"]
    return SettingsModel(
        system_prompt=llm_client.system_prompt,
        model_name=llm_client.model_name,
        indexed_folders=[IndexedFolder(path=fld, index_type="documentation") for fld in doc_folder_to_index]
                        + [IndexedFolder(path=fld, index_type="code_javascript") for fld in js_code_folder_to_index],
        indexation_frequency=index_frequency
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    # Load the environment variables
    load_dotenv()
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True 
    )