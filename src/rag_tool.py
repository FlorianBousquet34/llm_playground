from dotenv import load_dotenv
from pydantic_ai import Agent

from llm_model import LocalLLMModel
from utils_neo4j import perform_vector_search
from utils import build_context_from_results

# Load the environment variables
load_dotenv()

model = LocalLLMModel()

# Create PydanticAI Agent
agent = Agent(
    model=model,
    system_prompt=(
        "Answer the user's question.",
        "Use the similarity search tool for finding specific data in the database.",
    ),
)


# Define the retrieval tool
@agent.tool_plain
def perform_similarity_search(query: str) -> str:
    """
    Perform a similarity or vector search on the database.
    This is best used for finding important which have semantic similarity to the user's question.

    Args:
        query (str): A concise question for which you need to get the most relevant information.
    """
    print("Similarity search tool was called:", query)

    results = perform_vector_search(query, top_k=10)
    return build_context_from_results(results)


def main():
    query = "What are Pikachu's electric type moves?"
    result = agent.run_sync(query)
    print(result.output)


if __name__ == "__main__":
    main()
