from ollama import ChatResponse, chat

def call_ollama_llm_model(messages: list, system_prompt, model_name="qwen3.5:2b", tools = []) -> ChatResponse:
    messages.append({"role": "system", "content": system_prompt})
    response = chat(
        model=model_name,
        messages=messages,
        tools=[{"type": "function", "function": tool} for tool in tools]
    )
    
    return response