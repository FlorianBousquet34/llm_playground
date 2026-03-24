import datetime
import json
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic_ai import UsageLimits
import uvicorn
from src.api_models import ChatCreationModel, ChatModel, ChatRequest, ChatResponse, IndexedFolder, LoadedChat, SettingsModel
from src.chat_crud import save_exchange, save_question, save_response
from dynamic_injection_batch import INDEXATION_CONFIGURATION_FILE
from src.postgresconnector import close, commit, fetch_all, fetch_one, init_postgres, insert
from src.llm_client import OllamaLLMClient
from src.rag_tool import get_agent
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

@app.post("/new-chat", response_model=ChatModel)
def new_chat(chat_creation_model: ChatCreationModel):
    conn = init_postgres()
    model = {
        "chat_id": str(uuid.uuid4()),
        "chat_name": chat_creation_model.chat_name,
        "creation_date": datetime.datetime.now(tz=datetime.UTC)
    }
    insert("CHAT", model, conn)
    close(conn)
    return ChatModel(chat_id=model["chat_id"],
                     creation_date=datetime.datetime.strftime(model["creation_date"], '%Y-%m-%d %H:%M:%S.%f'),
                     chat_name=model["chat_name"])

@app.get("/chats", response_model=list[ChatModel])
def get_chats():
    conn = init_postgres()
    chats = fetch_all("select chat_id, chat_name, creation_date from chat", conn=conn)
    close(conn)
    return [
        ChatModel(chat_id=chat[0],
                  chat_name=chat[1],
                  creation_date=datetime.datetime.strftime(chat[2], '%Y-%m-%d %H:%M:%S.%f'))
        for chat in chats
    ]

@app.get("/chat/{chat_id}", response_model=LoadedChat)
def load_chat(chat_id: str):
    conn = init_postgres()
    chat = fetch_one(f"select chat_id, chat_name, creation_date from chat where chat_id = '{chat_id}'", conn=conn)
    questions = fetch_all("select chat_exchange.chat_exchange_id, user_prompt, asked_date, user_role, message_content, history_order, chat_exchange.chat_id " +
                            "from chat_question " +
                            "join chat_exchange on chat_exchange.chat_exchange_id = chat_question.chat_exchange_id " +
                            "left join chat_question_history on chat_question_history.chat_question_id = chat_question.chat_question_id "+
                            f"where chat_exchange.chat_id = '{chat_id}'", conn=conn)
    answers = fetch_all("select chat_exchange.chat_exchange_id, assistant_response, chat_answer_history.chat_answer_history_id, user_role, message_content, " +
                            "chat_answer_history.tool_name, thinking, history_order, chat_answer_history_tool_call.tool_name, chat_answer_history_tool_call.chat_answer_history_tool_call_id, " +
                            "argument_name, argument_value, chat_exchange.chat_id, creation_date " +
                            "from chat_answer " +
                            "join chat_exchange on chat_exchange.chat_exchange_id = chat_answer.chat_exchange_id " +
                            "left join chat_answer_history on chat_answer_history.chat_answer_id = chat_answer.chat_answer_id "+
                            "left join chat_answer_history_tool_call on chat_answer_history.chat_answer_history_id = chat_answer_history_tool_call.chat_answer_history_id "+
                            "left join chat_answer_history_tool_argument on chat_answer_history_tool_argument.chat_answer_history_tool_call_id = chat_answer_history_tool_call.chat_answer_history_tool_call_id "+
                            f"where chat_exchange.chat_id = '{chat_id}'", conn=conn)
    exchange_dict = {}
    for q in questions:
        if exchange_dict.get(q[6], None) is None:
            exchange_dict[q[6]] = {}
        if exchange_dict[q[6]].get(q[0], None) is None:
            exchange_dict[q[6]][q[0]] = {}
        if exchange_dict[q[6]][q[0]].get("question", None) is None:
            exchange_dict[q[6]][q[0]]["question"] = {
                "user_prompt": q[1],
                "asked_date": datetime.datetime.strftime(q[2], '%Y-%m-%d %H:%M:%S.%f')
            }
        if q[5] is not None:
            if exchange_dict[q[6]][q[0]]["question"].get("history", None) is None:
                exchange_dict[q[6]][q[0]]["question"]["history"] = []
            exchange_dict[q[6]][q[0]]["question"]["history"].append({
                "user_role": q[3],
                "message_content": q[4],
                "history_order": int(q[5])
            })
        else:
            exchange_dict[q[6]][q[0]]["question"]["history"] = []
            
    for r in answers:
        if exchange_dict.get(r[12], None) is None:
            exchange_dict[r[12]] = {}
        if exchange_dict[r[12]].get(r[0], None) is None: 
            exchange_dict[r[12]][r[0]] = {}
        if exchange_dict[r[12]][r[0]].get("response", None) is None:
            exchange_dict[r[12]][r[0]]["response"] = {
                "assistant_response": r[1],
                "creation_date": datetime.datetime.strftime(r[13], '%Y-%m-%d %H:%M:%S.%f')
            }
        if exchange_dict[r[12]][r[0]]["response"].get("history", None) is None:
            exchange_dict[r[12]][r[0]]["response"]["history"] = {}
        exchange_dict[r[12]][r[0]]["response"]["history"][r[2]] = {
            "user_role": r[3],
            "message_content": r[4],
            "tool_name": r[5],
            "thinking": r[6],
            "history_order": int(r[7])
        }
        if r[9] is not None:
            if exchange_dict[r[12]][r[0]]["response"]["history"][r[2]].get("tool_calls", None) is None:
                exchange_dict[r[12]][r[0]]["response"]["history"][r[2]]["tool_calls"] = {}
            exchange_dict[r[12]][r[0]]["response"]["history"][r[2]]["tool_calls"][r[9]] = {
                "tool_name": r[8]
            }
            if r[10] is not None:
                if exchange_dict[r[12]][r[0]]["response"]["history"][r[2]]["tool_calls"][r[9]].get("arguments", None) is None:
                    exchange_dict[r[12]][r[0]]["response"]["history"][r[2]]["tool_calls"][r[9]]["arguments"] = {}
                exchange_dict[r[12]][r[0]]["response"]["history"][r[2]]["tool_calls"][r[9]]["arguments"][r[10]] = r[11]
            else:
                exchange_dict[r[12]][r[0]]["response"]["history"][r[2]]["tool_calls"][r[9]]["arguments"] = {}
        else:
            exchange_dict[r[12]][r[0]]["response"]["history"][r[2]]["tool_calls"] = {}
    exchanges = exchange_dict.get(chat[0], None)
    if exchanges is not None:
        for e in exchanges.values():
            if e.get("question", None) is None:
                e["question"] = None
            if e.get("response", None) is None:
                e["response"] = None
    response = LoadedChat(chat_id=chat[0],
                chat_name=chat[1],
                creation_date=datetime.datetime.strftime(chat[2], '%Y-%m-%d %H:%M:%S.%f'),
                exchanges=exchanges.values() if exchanges is not None else [])
    close(conn)
    return response
    

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(chat_req: ChatRequest):
    # Run the agent with the provided history
    conn = init_postgres()
    req_id = str(uuid.uuid4())
    agent = get_agent()
    llm_client: OllamaLLMClient = agent.model.client
    csr = save_exchange(req_id, chat_req.chat_id, conn)
    csr = save_question(req_id, chat_req, llm_client.system_prompt, csr)
    commit(conn)
    llm_client.history[req_id] = []
    result = agent.run_sync(
        user_prompt=chat_req.user_query,
        message_history=chat_req.message_history,
        usage_limits=UsageLimits(request_limit=5, tool_calls_limit=3),
        metadata={"req_id": req_id}
    )
    history = llm_client.history.pop(req_id, None)
    save_response(result.response, history, req_id, conn)
    commit(conn)
    close(conn)
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