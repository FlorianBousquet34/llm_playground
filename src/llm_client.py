import datetime
from pydantic_ai.models.openai import AsyncOpenAI
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion import ChatCompletionMessage
from llm_loader import call_llm_model
import uuid
import json
from openai.types.chat.chat_completion_message_function_tool_call import ChatCompletionMessageFunctionToolCall, Function


class LocalLLMClient(AsyncOpenAI):
    
    def __init__(self, model_name="deepseek-ai/deepseek-coder-1.3b-instruct", api_key = None, organization = None, project = None, base_url = None, websocket_base_url = None, timeout = ..., max_retries = ..., default_headers = None, default_query = None, http_client = None, _strict_response_validation = False):
        super().__init__(api_key=api_key, organization=organization, project=project, base_url=base_url, websocket_base_url=websocket_base_url, timeout=timeout, max_retries=max_retries, default_headers=default_headers, default_query=default_query, http_client=http_client, _strict_response_validation=_strict_response_validation)
        self.model_name = model_name
    
    async def request(self, cast_to, options, *args, **kwargs) -> ChatCompletion:
        messages = options.json_data["messages"]
        http_tools = options.json_data["tools"]
        tools = [tool[tool["type"]] for tool in http_tools]
        #tools = [perform_graph_search, perform_similarity_search]
        question, resp = call_llm_model(messages, self.model_name, tools)
        print(f"QUESTION:\n{question}\nRESPONSE:\n{resp}")
        try:
            json_model = json.loads(resp)
            if json_model is not None:
                tool_calls = json_model.get("toolCalls", None)
                if tool_calls is not None and len(tool_calls) > 0:
                    return ChatCompletion(
                        id=str(uuid.uuid4()),
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
                                            name=call["name"],
                                            arguments=json.dumps(call["arguments"])
                                        )
                                    )
                                    for call in tool_calls
                                ]
                            ))
                        ]
                    )
        except:
            return ChatCompletion(
                id=str(uuid.uuid4()),
                model=self.model_name,
                object="chat.completion",
                created=int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
                choices=[
                    Choice(finish_reason="stop", index=0, message=ChatCompletionMessage(
                        content=resp,
                        role="assistant"
                        ))])
