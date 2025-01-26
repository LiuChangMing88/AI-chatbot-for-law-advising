import py_vncorenlp
import os
import json
from pathlib import Path
from pprint import pprint
import nltk
from langchain.llms import HuggingFaceHub
import uuid
from transformers import AutoModel, AutoTokenizer
from langchain.embeddings import HuggingFaceEmbeddings
from qdrant_client import QdrantClient, models
from typing import List, Dict, Tuple
from datetime import datetime
from tqdm import tqdm
import logging
from sentence_transformers import SentenceTransformer

# Create directory with error handling
save_dir = 'Preprocessing/Data'
try:
    os.makedirs(save_dir, exist_ok=True)
except OSError as e:
    print(f"Error creating directory: {e}")

# Download model to specific directory
py_vncorenlp.download_model(save_dir=save_dir)

# Load the word and sentence segmentation component
rdrsegmenter = py_vncorenlp.VnCoreNLP(
    annotators=["wseg"], 
    save_dir=save_dir
)

from langchain_community.document_loaders import JSONLoader

file_path = 'Preprocessing/Preprocess.py'
data = json.loads(Path(file_path).read_text())


QDRANT_API_KEY = ""
QDRANT_URL = ""
HUGGINGFACE_API_KEY= ""
QDRANT_COLLECTION_NAME = ""

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DualEmbeddings:
    def __init__(self, model1_name: str, model2_name: str):
        self.embeddings1 = HuggingFaceEmbeddings(model_name=model1_name)
        self.embeddings2 = HuggingFaceEmbeddings(model_name=model2_name)
        # Use first model's tokenizer for chunking
        self.tokenizer = SentenceTransformer(model1_name).tokenizer
        
    def embed_text(self, text: str) -> Tuple[List[float], List[float]]:
        return (
            self.embeddings1.embed_query(text),
            self.embeddings2.embed_query(text)
        )

# Initialize dual embeddings
embedder = DualEmbeddings(
    "truro7/vn-law-embedding",
    "tranguyen/halong_embedding-legal-document-finetune"
)

# Initialize Qdrant client
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, prefer_grpc=False)

def dynamic_chunk(
    text: str, 
    tokenizer, 
    title: str, 
    law_id: str, 
    max_tokens: int = 512, 
    overlap: int = 0
) -> List[str]:
    """
    Splits text into chunks, dynamically adjusts for metadata length, and includes metadata in each chunk.
    """
    if not text or not isinstance(text, str):
        return []

    # Calculate token length of metadata
    metadata = f"Title: {title}\nLaw ID: {law_id}\n"
    metadata_tokens = tokenizer.tokenize(metadata)
    metadata_token_length = len(metadata_tokens)

    # Adjust max_tokens to account for metadata
    adjusted_max_tokens = max_tokens - metadata_token_length

    if adjusted_max_tokens <= 0:
        raise ValueError("Metadata token length exceeds max_tokens. Consider shortening metadata or increasing max_tokens.")

    sentences = nltk.sent_tokenize(text)
    chunks, current_chunk = [], []
    current_length = 0

    for sentence in sentences:
        tokens = tokenizer.tokenize(sentence)
        if current_length + len(tokens) > adjusted_max_tokens:
            # Add metadata to chunk before appending
            chunk_with_metadata = (
                metadata +
                tokenizer.convert_tokens_to_string(current_chunk)
            )
            chunks.append(chunk_with_metadata)
            # Reset chunk with overlap if specified
            current_chunk = current_chunk[-overlap:] if overlap > 0 else []
            current_length = len(current_chunk)
        current_chunk.extend(tokens)
        current_length += len(tokens)

    # Add the last chunk with metadata
    if current_chunk:
        chunk_with_metadata = (
            metadata +
            tokenizer.convert_tokens_to_string(current_chunk)
        )
        chunks.append(chunk_with_metadata)

    return chunks


def process_and_ingest_chunk(
    chunk: str,
    article: Dict,
    law_id: str,
    embedder: DualEmbeddings,
    client: QdrantClient
):
    try:
        # Get both embeddings for the chunk with metadata
        chunk_embedding1, chunk_embedding2 = embedder.embed_text(chunk)
        
        point = models.PointStruct(
            id=str(uuid.uuid4()),
            payload={
                "chunk_text": chunk,
                "article_id": article['article_id'],
                "title": article['title'],
                "law_id": law_id,
                "timestamp": datetime.now().isoformat()
            },
            vector={
                "vn-law-embedding": chunk_embedding1,
                "halong_embedding": chunk_embedding2
            }
        )
        client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=[point])
        logger.info(f"Chunk successfully ingested: {point.id}")

    except Exception as e:
        logger.error(f"Error processing chunk: {str(e)}")
        raise


def ingest_to_qdrant(data: List[Dict], embedder: DualEmbeddings):
    for law in tqdm(data, desc="Processing laws"):
        if not law.get('articles'):
            logger.warning(f"No articles found for law_id: {law.get('law_id')}")
            continue
        
        for article in law['articles']:
            chunks = dynamic_chunk(
                text=article['text'], 
                tokenizer=embedder.tokenizer,
                title=article['title'], 
                law_id=law['law_id'], 
                max_tokens=512, 
                overlap=0
            )
            for chunk in chunks:
                process_and_ingest_chunk(
                    chunk=chunk,
                    article=article,
                    law_id=law['law_id'],
                    embedder=embedder,
                    client=client
                )


# Create collection with vector configurations for both embeddings
def setup_collection():
    client.create_collection(
        QDRANT_COLLECTION_NAME,
        vectors_config={
            "vn-law-embedding": models.VectorParams(
                size=768,
                distance=models.Distance.COSINE
            ),
            "halong_embedding": models.VectorParams(
                size=768,
                distance=models.Distance.COSINE
            )
        }
    )

if __name__ == "__main__":
    nltk.download('punkt')
    setup_collection()
    ingest_to_qdrant(data, embedder)