from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from llm_client import LocalLLMClient
from utils_neo4j import perform_code_search, perform_vector_search
from utils import build_context_from_graph_results, build_context_from_results
from pydantic_ai.providers.openai import OpenAIProvider
# Load the environment variables
load_dotenv()

client = LocalLLMClient("NousResearch/Hermes-3-Llama-3.2-3B")
model = OpenAIChatModel("", provider = OpenAIProvider(openai_client = client))

# Create PydanticAI Agent
agent = Agent(
    model=model
)


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
def perform_graph_search(query: str) -> str:
    """
    Perform a graph search on the code graph database.
    This is best used for finding important code related to the user's question.
    It should be called for question regarding my code base.

    Args:
        query (str): Keywords for which you need to get the most relevant information.
    """
    print("Graph search tool was called:", query)

    results = perform_code_search(query)
    return build_context_from_graph_results(results)


query = "Where is the function isNumberPrime in my code base ?"
result = agent.run_sync(query)