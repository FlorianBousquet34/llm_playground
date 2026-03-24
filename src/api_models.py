from ollama import Message
from pydantic import BaseModel
from typing import List
from pydantic_ai.messages import ModelResponse, ModelMessage

class ChatRequest(BaseModel):
    chat_id: str
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
    
class ChatModel(BaseModel):
    chat_id: str
    creation_date: str
    chat_name: str

class ChatCreationModel(BaseModel):
    chat_name: str
    
class ChatQuestionHistory(BaseModel):
    user_role: str
    message_content: str
    history_order: int

class LoadedChatQuestion(BaseModel):
    user_prompt: str
    asked_date: str
    history: list[ChatQuestionHistory]

class ChatResponseToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, str] | None

class ChatResponseHistory(BaseModel):
    user_role: str
    message_content: str | None
    tool_name: str | None
    thinking: str | None
    history_order: int
    tool_calls: dict[str, ChatResponseToolCall]

class LoadedChatResponse(BaseModel):
    assistant_response: str
    creation_date: str
    history: dict[str, ChatResponseHistory]

class LoadedChatExchange(BaseModel):
    question: LoadedChatQuestion | None
    response: LoadedChatResponse | None

class LoadedChat(BaseModel):
    chat_id: str
    creation_date: str
    chat_name: str
    exchanges: list[LoadedChatExchange]