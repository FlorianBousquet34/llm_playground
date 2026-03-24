from dotenv import load_dotenv
from neomodel import StructuredNode, StringProperty, config, ArrayProperty

from src.utils_neo4j import clear_db_file
from src.text_embedding import OllamaEmbeddingModel
from src.utils import read_file_as_object_array, recursive_text_splitter

# Configure the database connection
config.DATABASE_URL = 'bolt://neo4j:password@localhost:7687'

class DocumentNode(StructuredNode):
    content = StringProperty()
    filename = StringProperty()
    vector = ArrayProperty()

# Load environment variables
load_dotenv()

def refresh_files(file_paths, chunck_size=512, overlap_length=100, model_chunk_size=512):
    # Read the files
    print(f"Updating {len(file_paths)} documentation files...")
    file_array = []
    for file_path in file_paths:
        if file_path.endswith(".md"):
            file_object = read_file_as_object_array(file_path)
            if file_object is not None:
                file_array.append(file_object)

    # Clear db 
    clear_db_file(file_paths)

    if len(file_array) > 0:

        # Split the markdown files into chunks
        splits = recursive_text_splitter(file_array, chunck_size, overlap_length)

        # Prepare an array of string from the documents
        splits_as_string = [
            f"{doc.metadata.get('filename', '')}\n{doc.page_content}\n" for doc in splits
        ]

        # Compute the embeddings
        embeddings = OllamaEmbeddingModel.embed_documents(splits_as_string, chunk_size=model_chunk_size, log_progess=True)

        # Save the embeddings to libsql
        # Insert the embeddings into the database
        for i, embedding in enumerate(embeddings):
            DocumentNode(vector=embedding, content=splits[i].page_content, filename=splits[i].metadata["filename"]).save()

        print("Updating documentation done!")
