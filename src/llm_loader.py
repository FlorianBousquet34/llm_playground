from ollama import ChatResponse, chat

def call_ollama_llm_model(messages: list, model_name="qwen3.5:2b", tools = None) -> ChatResponse:
    messages.append({"role": "system", "content": "You are a function calling AI model. You are provided with function signatures. You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into functions."})
    response = chat(
        model=model_name,
        messages=messages,
        tools=[{"type": "function", "function": tool} for tool in tools]
    )
    
    return response