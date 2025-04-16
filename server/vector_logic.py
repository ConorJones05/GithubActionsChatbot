# Standard library imports
import os
import logging
from typing import List, Dict, Any, Tuple, Optional, Union

# Third-party imports
import openai
import tiktoken
import numpy as np
import pandas as pd
from pinecone import Pinecone, ServerlessSpec
from sklearn.cluster import KMeans
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("vector_logic")

openai_key = os.environ.get("OPENAI_KEY")
client = openai.OpenAI(api_key=openai_key)

pinecone_key = os.environ.get("PINECONE_KEY")
pc = Pinecone(api_key=pinecone_key)


# ----- Pydantic Models -----

class VectorMetadata(BaseModel):
    """Metadata for vector entries"""
    genre: str
    api_key: str
    issue: str
    timestamp: str
    
    class Config:
        validate_assignment = True


class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation"""
    model: str = "text-embedding-3-small"
    dimensions: int = 1536
    
    @validator('model')
    def validate_model_name(cls, v):
        valid_models = ["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"]
        if v not in valid_models:
            raise ValueError(f"Model must be one of: {', '.join(valid_models)}")
        return v


class ClusteringConfig(BaseModel):
    """Configuration for clustering"""
    n_clusters: int = Field(default=8, ge=2, le=100)
    index_name: str = "github-actions-errors"
    random_state: int = 42
    n_init: int = 10


class PineconeIndexConfig(BaseModel):
    """Configuration for Pinecone index"""
    name: str = "github-actions-errors"
    dimension: int = 1536
    metric: str = "cosine"
    cloud: str = "aws"
    region: str = "us-west-2"


class ClusteringResult(BaseModel):
    """Results from clustering operation"""
    success: bool
    dataframe: Optional[Dict] = None
    kmeans: Optional[Dict] = None
    error: Optional[str] = None
    n_clusters: int
    
    @classmethod
    def from_error(cls, error: str, n_clusters: int) -> "ClusteringResult":
        return cls(
            success=False,
            error=str(error),
            n_clusters=n_clusters
        )


# ----- Embedding and Token Functions -----

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


def vector_embeddings(
    text: str, 
    config: Optional[EmbeddingConfig] = None
) -> List[float]:
    """Generate vector embeddings for the given text."""
    if config is None:
        config = EmbeddingConfig()
        
    try:
        response = client.embeddings.create(
            model=config.model, 
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to create embeddings: {str(e)}")
        raise RuntimeError(f"Embedding creation failed: {str(e)}")


# ----- Clustering Functions -----

def clustering_classify(
    config: Optional[ClusteringConfig] = None
) -> Tuple[pd.DataFrame, KMeans]:
    """Classify vectors into clusters using KMeans."""
    if config is None:
        config = ClusteringConfig()
        
    try:
        index = pc.Index(config.index_name)
        
        query_response = index.query(
            vector=[0.0] * 1536, 
            top_k=1000,
            include_values=True
        )
        
        vectors = [match["values"] for match in query_response["matches"]]
        
        if not vectors:
            logger.warning("No vectors found in index for clustering")
            return pd.DataFrame(), None
            
        kmeans = KMeans(n_clusters=min(config.n_clusters, len(vectors)), random_state=config.random_state, n_init=config.n_init)
        cluster_labels = kmeans.fit_predict(vectors)
        
        ids = [match["id"] for match in query_response["matches"]]
        
        return pd.DataFrame({"id": ids, "cluster": cluster_labels}), kmeans
    except Exception as e:
        logger.error(f"Error in clustering: {str(e)}")
        return pd.DataFrame(), None


def add_vector(vector_id: str, vector_values: List[float], metadata: VectorMetadata) -> bool:
    """Add a vector to the Pinecone index."""
    try:
        index_name = "github-actions-errors"
        
        if index_name not in [idx.name for idx in pc.list_indexes()]:
            pc.create_index(
                name=index_name,
                dimension=len(vector_values),
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",  # Changed from 'aws' to 'gcp'
                    region="us-east1-gcp"  # Changed from 'us-west-2' to 'us-east1-gcp'
                )
            )
            logger.info(f"Created new index: {index_name}")
        
        index = pc.Index(index_name)
        
        # Convert metadata datetime objects to strings if needed
        metadata_dict = metadata.dict()
        
        index.upsert(
            vectors=[(vector_id, vector_values, metadata_dict)]
        )
        
        logger.info(f"Vector added successfully with ID {vector_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to add vector to database: {str(e)}")
        return False