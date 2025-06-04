import os

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
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


def markdown_splitter(data, chunk_size, overlap_size):
    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")],
        strip_headers=True,
    )

    md_splits = [md_splitter.split_text(text["content"]) for text in data]

    # Make sure we add the filename to the metadata
    for i, page in enumerate(md_splits):
        for split in page:
            split.metadata["filename"] = data[i]["filename"]

    # Flatten the list of lists
    md_splits = [split for sublist in md_splits for split in sublist]

    # Don't forget to contraint split size
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap_size,
        length_function=len,
        is_separator_regex=False,
    )

    return text_splitter.split_documents(md_splits)

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
    return "---\n".join(
        [
            f"Title: {result['filename']}\nContent:\n{result['content']}\n"
            for result in results
        ]
    )