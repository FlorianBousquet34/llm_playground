from typing import Optional

from neo4j import GraphDatabase, RoutingControl

from text_embedding import embed_documents

def perform_vector_search(query: str, pokemon: Optional[str] = None, top_k: int = 5):
    uri = "neo4j://localhost:7687"
    auth = ("neo4j", "password")

    # Create the embedding for the query
    embedding = embed_documents([query])[0]

    # Perform the vector search
    with GraphDatabase.driver(uri, auth=auth) as driver:
        results = driver.execute_query(
                """
                    MATCH (m:DocumentNode)
                    WHERE m.filename = $pokemon OR $pokemon is null
                    WITH m, vector.similarity.cosine(m.vector, $embedding) AS score
                    RETURN m.content AS content, m.filename AS filename, score
                    ORDER BY score DESC
                    LIMIT $limit
                """,
                limit=top_k, embedding=embedding.tolist(), pokemon=pokemon,
                database_="neo4j", routing_=RoutingControl.READ
            )
    return list(map(lambda x: {r:x[r] for r in results.keys}, results.records))