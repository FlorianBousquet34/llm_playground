import os

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

def recursive_text_splitter(data, chunk_size, overlap_size):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap_size,
        length_function=len,
        is_separator_regex=False,
    )

    texts = text_splitter.create_documents(
        [f"{text["filename"]}\n{text["content"]}" for text in data],
        metadatas=[dict({"filename": text["filename"]}) for text in data],
    )
    return texts

def read_file_as_object_array(file_path):
    """
    Reads a file at the specified path and returns their contents as objects.

    The object contains the filename and the content of the file.

    Args:
        file_path (str): Path to the the file.

    Returns:
        object: a dictionary, where with 'filename' and 'content' keys.
    """
    if os.path.isfile(file_path):
        try:
            # Read the content of the file
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            # Append the file name and content as an object to the array
            return {"filename": file_path, "content": content}
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
    
    return None

def build_context_from_results(results):
    return "\n".join(
        [
            f"In the file {result['filename']} there is the following content {result['content']}\n"
            for result in results
        ]
    )
    

def build_context_from_graph_results(results):
    nodes = [result[0] for result in results] + [result[2] for result in results]
    nodes = {v:k for k,v in enumerate(list(set(nodes)))}
    
    return ("\n".join([
        f"Node {v} is \nFile: {k[0]['filename']}\nType: {k[0]['node_type']}\nContent:\n{k[0]['content']}\n"
        for v,k in enumerate(nodes.items())
        if k[0]['node_type'] not in ["statement_block", "program"]
        ]
        ) +
        "\n".join(
        [
            f"Node {nodes[result[0]]} {result[1].type} Node {nodes[result[2]]}"
            for result in results
        ])
    )