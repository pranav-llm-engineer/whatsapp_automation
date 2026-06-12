import chromadb
from chromadb.utils import embedding_functions
from backend.config import CHROMA_DB_PATH, EMBEDDING_MODEL, OPENROUTER_API_KEY

# Initialize client globally to reuse connection
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

def retrieve_context(query: str, top_k: int = 5) -> str:
    """
    Embed query -> similarity search ChromaDB -> return top_k chunks as string with headers reconstructed
    """
    results = collection.query(query_texts=[query], n_results=top_k, include=["documents", "metadatas"])
    if not results or not results["documents"] or not results["documents"][0]:
        return ""
        
    contexts = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        heading = ""
        if "Category" in meta:
            heading += f"## {meta['Category']}\n"
        if "Topic" in meta:
            heading += f"### {meta['Topic']}\n"
        contexts.append(heading + doc)
        
    return "\n\n---\n\n".join(contexts)
