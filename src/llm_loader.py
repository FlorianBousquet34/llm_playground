from ollama import ChatResponse, chat

def call_ollama_llm_model(messages, model_name="llama3", tools = None) -> ChatResponse:
    
    response = chat(
        model=model_name,
        messages=messages,
        tools=[{"type": "function", "function": tool} for tool in tools]
    )
    
    return response