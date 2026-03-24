
import datetime
import json
from uuid import uuid4

from pydantic_ai import ModelResponse

from src.api_models import ChatRequest
from src.postgresconnector import batch_insert


def save_exchange(req_id: str, chat_id: str, conn):
    model = {
        "chat_exchange_id": req_id,
        "chat_id": chat_id,
        "exchange_date": datetime.datetime.now(datetime.UTC)
    }
    return batch_insert("CHAT_EXCHANGE", model, conn=conn)

def save_question(req_id, chat_request: ChatRequest, system_promt, csr):
    question_uuid = str(uuid4())
    model = {
        "chat_question_id": question_uuid,
        "chat_exchange_id": req_id,
        "user_prompt": chat_request.user_query,
        "system_prompt": system_promt,
        "asked_date": datetime.datetime.now(datetime.UTC)
    }
    csr = batch_insert("CHAT_QUESTION", model, cursor=csr)
    
    for ih, h in enumerate(chat_request.message_history):
        history_uuid = str(uuid4())
        model = {
            "chat_question_history_id": history_uuid,
            "chat_question_id": question_uuid,
            "user_role": h.kind,
            "message_content": h.parts[0].content,
            "history_order": ih
        }
        csr = batch_insert("CHAT_QUESTION_HISTORY", model, cursor=csr)
    return csr

def save_response(response: ModelResponse, history: list[dict], req_id: str, conn):
    response_uuid = str(uuid4())
    model = {
        "chat_answer_id": response_uuid,
        "chat_exchange_id": req_id,
        "assistant_response": response.parts[0].content,
        "creation_date": datetime.datetime.now(datetime.UTC)
    }
    csr = batch_insert("CHAT_ANSWER", model, conn=conn)
    for ih, h in enumerate(history):
        history_uuid = str(uuid4())
        model = {
            "chat_answer_history_id": history_uuid,
            "chat_answer_id": response_uuid,
            "user_role": h.get("role", None),
            "message_content": h.get("content", None),
            "tool_name": h.get("tool_name", None),
            "thinking": h.get("thinking", None),
            "history_order": ih
        }
        csr = batch_insert("CHAT_ANSWER_HISTORY", model, cursor=csr)
        if h.get("tool_calls", None) is not None and len(h["tool_calls"]) > 0:
                for call in h["tool_calls"]:
                    tool_call_id = str(uuid4())
                    model = {
                        "chat_answer_history_tool_call_id": tool_call_id,
                        "chat_answer_history_id": history_uuid,
                        "tool_name": call.get("function", {}).get("name", None),
                    }
                    csr = batch_insert("CHAT_ANSWER_HISTORY_TOOL_CALL", model, cursor=csr)
                    if call.get("function", {}).get("arguments", None) is not None and len(call["function"]["arguments"]) > 0:
                        argument_dict: dict = call["function"]["arguments"]
                        for argum_name in argument_dict.keys():
                            model = {
                                "chat_answer_history_tool_argument_id": str(uuid4()),
                                "chat_answer_history_tool_call_id": tool_call_id,
                                "argument_name": argum_name,
                                "argument_value": json.dumps(argument_dict[argum_name])
                            }
                            csr = batch_insert("CHAT_ANSWER_HISTORY_TOOL_ARGUMENT", model, cursor=csr)
    return csr