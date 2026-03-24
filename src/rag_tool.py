from os import getenv

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai import Agent
from src.llm_client import OllamaLLMClient
from src.utils_neo4j import perform_code_search, perform_vector_search
from src.utils import build_context_from_graph_results, build_context_from_results
from pydantic_ai.providers.openai import OpenAIProvider
from src.webtool import perform_google_search


client = OllamaLLMClient(api_key="", model_name=getenv("DEFAULT_LLM_MODEL"))
model = OpenAIChatModel("", provider = OpenAIProvider(openai_client = client))

# Create PydanticAI Agent
agent = Agent(
    model=model
)

def get_agent():
    return agent


@agent.tool_plain
def perform_similarity_search(query: str, _req_id: str = None) -> str:
    """
    Perform a similarity search on the documentation.
    This is best used for finding important documentation which have semantic
    similarity to the user's question.
    Use in priority for questions regarding specification.

    Args:
        query (str): A concise question for which you need to get the most relevant information.
    """
    print("Similarity search tool was called:", query)

    results = perform_vector_search(query, top_k=10)
    response = build_context_from_results(results)
    agent.model.client.history[_req_id].append({
        "role": "tool",
        "tool_name": "perform_similarity_search",
        "content": response
    })
    return response

@agent.tool_plain
def perform_graph_search(keyword_list: list[str], _req_id: str = None) -> str:
    """
    Perform a graph search on a tree sitter graph of my codebase.
    You can access my codebase using this tool.
    This is best used for finding important code related to the user's question.
    It must be called for question regarding my code base.
    The function searches for the given words in the code.
    Use in priority for questions regarding code.
    Do not use spaces.

    Args:
        query (list[str]): A list of Keywords for which you need to get the most relevant information.
    """
    print("Graph search tool was called:", keyword_list)

    results = [perform_code_search(q) for q in keyword_list]
    response = build_context_from_graph_results(list(set([r
        for res in results
        for r in res])))
    agent.model.client.history[_req_id].append({
        "role": "tool",
        "tool_name": "perform_graph_search",
        "content": response
    })
    return response

@agent.tool_plain
def web_search(query: str, _req_id: str = None) -> str:
    """
    Perform a google web search.
    You can access the web to get information with this tool.
    Use keywords for google.
    Use when you have no other option.
    
    Args:
        query (str): A concise question to search on google.
    """
    
    response = perform_google_search(query)
    agent.model.client.history[_req_id].append({
        "role": "tool",
        "tool_name": "web_search",
        "content": response
    })
    return response