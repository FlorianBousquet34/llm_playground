from dotenv import load_dotenv
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai import Agent
from src.llm_client import OllamaLLMClient
from src.utils_neo4j import perform_code_search, perform_vector_search
from src.utils import build_context_from_graph_results, build_context_from_results
from pydantic_ai.providers.openai import OpenAIProvider
# Load the environment variables
load_dotenv()

client = OllamaLLMClient(api_key="")
model = OpenAIChatModel("", provider = OpenAIProvider(openai_client = client))

# Create PydanticAI Agent
agent = Agent(
    model=model
)

def get_agent():
    return agent


# Define the retrieval tool
@agent.tool_plain
def perform_similarity_search(query: str) -> str:
    """
    Perform a similarity search on the documentation database.
    This is best used for finding important documentation which have semantic
    similarity to the user's question.

    Args:
        query (str): A concise question for which you need to get the most relevant information.
    """
    print("Similarity search tool was called:", query)

    results = perform_vector_search(query, top_k=10)
    return build_context_from_results(results)

# Define the retrieval tool
@agent.tool_plain
def perform_graph_search(query: list[str]) -> str:
    """
    Perform a search on the code database.
    You can access my codebase using this tool.
    This is best used for finding important code related to the user's question.
    It must be called for question regarding my code base.
    The function search for the given words in the code.
    Do not use spaces.

    Args:
        query (list[str]): Keywords for which you need to get the most relevant information.
    """
    print("Graph search tool was called:", query)

    results = [perform_code_search(q) for q in query]
    return build_context_from_graph_results(list(set([r
        for res in results
        for r in res])))