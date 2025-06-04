from dotenv import load_dotenv
from neo4j import GraphDatabase, RoutingControl
from neomodel import StructuredNode, StringProperty, config, ArrayProperty

# Configure the database connection
config.DATABASE_URL = 'bolt://neo4j:password@localhost:7687'

from text_embedding import embed_documents
from utils import read_file_as_object_array, recursive_text_splitter

class DocumentNode(StructuredNode):        
    content = StringProperty()
    filename = StringProperty()
    vector = ArrayProperty()

# Load environment variables
load_dotenv()

def refresh_files(file_paths, chunck_size=512, overlap_length=100, model_chunk_size=512):
    # Read the files
    print(f"Updating {len(file_paths)} files...")
    file_array = []
    for file_path in file_paths:
        file_object = read_file_as_object_array(file_path)
        if file_object is not None:
            file_array.append(file_object)
    
    # Clear db 
    uri = "neo4j://localhost:7687"
    auth = ("neo4j", "password")
    with GraphDatabase.driver(uri, auth=auth) as driver:
        driver.execute_query(
            """
                MATCH (n:DocumentNode)
                WHERE n.filename IN ($file_paths)
                DELETE n
            """,
            file_paths=file_paths,
            database_="neo4j", routing_= RoutingControl.WRITE
        )

    if len(file_array) > 0:
        
        # Split the markdown files into chunks
        splits = recursive_text_splitter(file_array, chunck_size, overlap_length)

        # Prepare an array of string from the documents
        splits_as_string = [
            f"{doc.metadata.get('filename', '')}\n{doc.page_content}\n" for doc in splits
        ]

        # Compute the embeddings
        embeddings = embed_documents(splits_as_string, chunk_size=model_chunk_size)

        # Save the embeddings to libsql
        # Insert the embeddings into the database
        for i, embedding in enumerate(embeddings):
            DocumentNode(vector=embedding.tolist(), content=splits[i].page_content, filename=splits[i].metadata["filename"]).save()
        
        print("Updating done!")    