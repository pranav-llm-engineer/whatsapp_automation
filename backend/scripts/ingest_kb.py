import os
import sys

# Add parent dir to path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_text_splitters import MarkdownHeaderTextSplitter
from backend.config import CHROMA_DB_PATH, EMBEDDING_MODEL, OPENROUTER_API_KEY
import chromadb
from chromadb.utils import embedding_functions

KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base", "cowork_kb.md")

def ingest():
    print(f"Reading {KB_PATH}...")
    with open(KB_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    print("Splitting text by markdown headers...")
    headers_to_split_on = [
        ("##", "Category"),
        ("###", "Topic"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(content)

    print(f"Created {len(md_header_splits)} chunks.")

    print(f"Initializing ChromaDB at {CHROMA_DB_PATH}...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    openrouter_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENROUTER_API_KEY,
        api_base="https://openrouter.ai/api/v1",
        model_name="openai/text-embedding-3-small"
    )

    collection = client.get_or_create_collection(
        name="cowork_kb",
        embedding_function=openrouter_ef
    )

    documents = []
    metadatas = []
    ids = []

    for i, chunk in enumerate(md_header_splits):
        documents.append(chunk.page_content)
        meta = chunk.metadata
        meta["source"] = "KB"
        # Ensure all metadata values are primitive types (strings, ints, floats, bools)
        for key in meta:
            if meta[key] is None:
                meta[key] = ""
            elif not isinstance(meta[key], (str, int, float, bool)):
                meta[key] = str(meta[key])
        metadatas.append(meta)
        ids.append(f"chunk_{i}")

    print("Upserting chunks to ChromaDB... this might take a moment.")
    collection.upsert(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print("Ingestion complete!")

if __name__ == "__main__":
    ingest()
