import datetime
from pydantic_ai.models.openai import AsyncOpenAI
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion import ChatCompletionMessage
from src.llm_loader import call_ollama_llm_model
import uuid
import json
from openai.types.chat.chat_completion_message_function_tool_call import ChatCompletionMessageFunctionToolCall, Function
from pydantic_ai._run_context import get_current_run_context

class OllamaLLMClient(AsyncOpenAI):
    def __init__(self, model_name="qwen3.5:2b", api_key = None, organization = None, project = None, base_url = None, websocket_base_url = None, timeout = ..., max_retries = ..., default_headers = None, default_query = None, http_client = None, _strict_response_validation = False):
        super().__init__(api_key=api_key, organization=organization, project=project, base_url=base_url, websocket_base_url=websocket_base_url, timeout=timeout, max_retries=max_retries, default_headers=default_headers, default_query=default_query, http_client=http_client, _strict_response_validation=_strict_response_validation)
        self.model_name = model_name
        self.history = {}
        # FIXME config file
        self.system_prompt = "You are a function calling AI model. You are provided with function signatures. You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into functions. Use the tool_calls json item in your response to invoke tools. Give short answers, summarize if needed."
        
    async def request(self, cast_to, options, *args, **kwargs) -> ChatCompletion:
        req_id = get_current_run_context().metadata["req_id"]
        messages = options.json_data["messages"]
        for message in messages:
            if message.get("tool_calls", None) is not None:
                for call in message["tool_calls"]:
                    if call.get("function", None) is not None and call["function"].get("arguments", None) is not None:
                        call["function"]["arguments"] = json.loads(call["function"]["arguments"])
                        call["function"]["arguments"].pop("_req_id", None)
        http_tools = options.json_data["tools"]
        tools = [tool[tool["type"]] for tool in http_tools]
        resp = call_ollama_llm_model(messages, self.system_prompt, self.model_name, tools)
        self.history[req_id].append(resp.message.__deepcopy__())
        if self.history[req_id][-1].get("tool_calls", None) is not None:
                for call in self.history[req_id][-1]["tool_calls"]:
                    if call.get("function", None) is not None and call["function"].get("arguments", None) is not None:
                        call["function"]["arguments"].pop("_req_id", None)
        resp_uuid = str(uuid.uuid4())
        print(f"RESPONSE:\n{resp.message}")
        if resp.message is not None and resp.message.tool_calls is not None and len(resp.message.tool_calls) > 0:
            tool_calls = resp.message.tool_calls
            for call in tool_calls:
                if call.function.arguments is None:
                    call.function.arguments = {"_req_id": req_id}
                else:
                    call.function.arguments["_req_id"] = req_id
            return ChatCompletion(
                        id=resp_uuid,
                        model=self.model_name,
                        object="chat.completion",
                        created=int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
                        choices=[
                            Choice(finish_reason="tool_calls", index=0, message=ChatCompletionMessage(
                                role="assistant",
                                tool_calls=[
                                    ChatCompletionMessageFunctionToolCall(
                                        id=str(uuid.uuid4()),
                                        type="function",
                                        function=Function(
                                            name=call.function.name,
                                            arguments=json.dumps(call.function.arguments)
                                        )
                                    )
                                    for call in tool_calls
                                ]
                            ))
                        ]
                    )
        else:
            return ChatCompletion(
                id=resp_uuid,
                model=self.model_name,
                object="chat.completion",
                created=int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
                choices=[
                    Choice(finish_reason="stop", index=0, message=ChatCompletionMessage(
                        content=resp.message.content,
                        role="assistant"
                        ))])