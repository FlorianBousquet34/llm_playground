from neo4j import GraphDatabase, RoutingControl

from text_embedding import embed_documents

uri = "neo4j://localhost:7687"
auth = ("neo4j", "password")
    
def perform_vector_search(query: str, top_k: int = 5):
    
    # Create the embedding for the query
    embedding = embed_documents([query])[0]

    # Perform the vector search
    with GraphDatabase.driver(uri, auth=auth) as driver:
        results = driver.execute_query(
                """
                    MATCH (m:DocumentNode)
                    WITH m, vector.similarity.cosine(m.vector, $embedding) AS score
                    RETURN m.content AS content, m.filename AS filename, score
                    ORDER BY score DESC
                    LIMIT $limit
                """,
                limit=top_k, embedding=embedding.tolist(),
                database_="neo4j", routing_=RoutingControl.READ
            )
    return list(map(lambda x: {r:x[r] for r in results.keys}, results.records))

def perform_code_search(query):
    
    # Perform the graph search
    with GraphDatabase.driver(uri, auth=auth) as driver:
        results = driver.execute_query(
            """
            MATCH (n:CodeNode)-[r]->(k:CodeNode)
            WHERE n.content CONTAINS $keyword AND NOT n.node_type IN ["identifier"]
            AND k.content CONTAINS $keyword AND NOT k.node_type IN ["identifier"]
            RETURN n,r,k
            """,
            keyword=query,
            database_="neo4j", routing_=RoutingControl.READ
        )
    return results[0]

def clear_db_file(file_paths):
    
    with GraphDatabase.driver(uri, auth=auth) as driver:
        driver.execute_query(
            """
                MATCH (n)
                WHERE n.filename IN ($file_paths)
                DETACH DELETE n
            """,
            file_paths=file_paths,
            database_="neo4j", routing_= RoutingControl.WRITE
            )