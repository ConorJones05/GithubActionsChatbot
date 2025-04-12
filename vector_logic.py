import openai
import tiktoken
import numpy as np
import pandas as pd
import pinecone
import os
import logging
from sklearn.cluster import KMeans
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Dict, Any, Tuple, Optional

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("vector_logic")

openai.api_key = os.environ.get("OPENAI_KEY")
client = openai

pinecone_key = os.environ.get("PINECONE_KEY")
pinecone.init(api_key=pinecone_key, environment="us-west-2")


class VectorMetadata(BaseModel):
    genre: str
    api_key: str
    issue: str
    timestamp: str


def token_checker(text: str, model_name: str) -> str:
    """Check and truncate tokens if they exceed the model's limit."""
    try:
        encoding = tiktoken.get_encoding(model_name) if model_name == "cl100k_base" else tiktoken.encoding_for_model(model_name)
        tokens = encoding.encode(text)
        max_tokens = 8000
        if len(tokens) > max_tokens:
            logger.warning(f"Truncating text from {len(tokens)} to {max_tokens} tokens")
            return encoding.decode(tokens[:max_tokens])
        return text
    except Exception as e:
        logger.error(f"Error in token checker: {str(e)}")
        raise RuntimeError(f"Failed to process tokens: {str(e)}")


def vector_embeddings(text: str) -> List[float]:
    """Generate vector embeddings for the given text."""
    try:
        response = client.Embedding.create(model="text-embedding-3-small", input=text)
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to create embeddings: {str(e)}")
        raise RuntimeError(f"Embedding creation failed: {str(e)}")


def predict_vector_cluster(vector: List[float]) -> int:
    """Predict the cluster for a given vector."""
    try:
        cluster_df, kmeans = clustering_classify()
        return kmeans.predict([vector])[0]
    except Exception as e:
        logger.error(f"Error predicting cluster: {str(e)}")
        raise RuntimeError(f"Cluster prediction failed: {str(e)}")


def clustering_classify(index_name: str = "github-actions-errors", n_clusters: int = 8) -> Tuple[pd.DataFrame, KMeans]:
    """Classify vectors into clusters using KMeans."""
    try:
        index = pinecone.Index(index_name)
        vectors = [match["values"] for match in index.query(vector=[0.0] * 1536, top_k=1000)["matches"]]
        kmeans = KMeans(n_clusters=min(n_clusters, len(vectors)), random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(vectors)
        return pd.DataFrame({"id": [match["id"] for match in vectors], "cluster": cluster_labels}), kmeans
    except Exception as e:
        logger.error(f"Error in clustering: {str(e)}")
        return pd.DataFrame(), None


def add_vector(vector_id: str, vector_values: List[float], metadata: VectorMetadata) -> bool:
    """Add a vector to the Pinecone index."""
    try:
        index_name = "github-actions-errors"
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(name=index_name, dimension=len(vector_values), metric="cosine")
        index = pinecone.Index(index_name)
        index.upsert(vectors=[(vector_id, vector_values, metadata.dict())])
        logger.info(f"Vector added successfully with ID {vector_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to add vector to database: {str(e)}")
        return False