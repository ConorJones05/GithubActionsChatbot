import openai
import tiktoken
import numpy as np
import pandas as pd
from ast import literal_eval
from pinecone import Pinecone, ServerlessSpec
import os
import logging
from sklearn.cluster import KMeans
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vector_logic')

logger.info("Initializing vector logic module...")
load_dotenv()

# Initialize OpenAI
openai.api_key = os.environ.get("OPENAI_KEY")
if not openai.api_key:
    logger.error("OpenAI API key not found! Application will not function correctly.")
    raise EnvironmentError("OpenAI API key not configured")
client = openai

# Initialize Pinecone
pinecone_key = os.environ.get("PINECONE_KEY")
if not pinecone_key:
    logger.error("Pinecone API key not found! Vector database functions will not work.")
    raise EnvironmentError("Pinecone API key not configured")

try:
    pc = Pinecone(api_key=pinecone_key)
    logger.info("Pinecone initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Pinecone: {str(e)}")
    raise RuntimeError(f"Pinecone initialization failed: {str(e)}")

def token_checker(text, model_name):
    try:
        if model_name == "cl100k_base":
            encoding = tiktoken.get_encoding(model_name)
        else:
            encoding = tiktoken.encoding_for_model(model_name)
        
        tokens = encoding.encode(text)
        token_count = len(tokens)
        logger.debug(f"Text contains {token_count} tokens")
        
        # Truncate if over limits (8k tokens for safety)
        max_tokens = 8000
        if token_count > max_tokens:
            logger.warning(f"Truncating text from {token_count} to {max_tokens} tokens")
            truncated_tokens = tokens[:max_tokens]
            return encoding.decode(truncated_tokens)
        return text
    except Exception as e:
        logger.error(f"Error in token checker: {str(e)}")
        raise RuntimeError(f"Failed to process tokens: {str(e)}")

def vector_embeddings(text):
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        logger.debug(f"Created embeddings with dimension {len(response.data[0].embedding)}")
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to create embeddings: {str(e)}")
        raise RuntimeError(f"Embedding creation failed: {str(e)}")

def predict_vector_cluster(vector):
    try:
        cluster_df, kmeans = clustering_classify()
        if kmeans is None:
            logger.error("Clustering model not available")
            raise ValueError("Clustering model could not be created")
            
        # Predict cluster for this vector
        cluster = kmeans.predict([vector])[0]
        logger.info(f"Vector assigned to cluster {cluster}")
        return int(cluster)
    except Exception as e:
        logger.error(f"Error predicting cluster: {str(e)}")
        raise RuntimeError(f"Cluster prediction failed: {str(e)}")

def distance(vector):
    try:
        index_name = "github-actions-errors"
        index = pc.Index(index_name)
        
        # Query for similar vectors
        query_response = index.query(
            vector=vector,
            top_k=5,
            include_metadata=True
        )
        
        similar_errors = []
        for match in query_response.matches:
            similar_errors.append({
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata
            })
        
        logger.info(f"Found {len(similar_errors)} similar vectors")
        return similar_errors
    except Exception as e:
        logger.error(f"Error in similarity search: {str(e)}")
        return []  # Return empty list as this is non-critical functionality

def add_vector(vector_id, vector_values, metadata):
    logger.info(f"Adding vector {vector_id} to database")
    
    try:
        # Check if the index exists, use a default index name
        index_name = "github-actions-errors"
        indexes = pc.list_indexes()
        
        if index_name not in [idx["name"] for idx in indexes]:
            logger.info(f"Creating new index: {index_name}")
            pc.create_index(
                name=index_name,
                dimension=len(vector_values),
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-west-2"
                )
            )
        
        # Get the index
        index = pc.Index(index_name)
        
        # Upsert the vector
        upsert_response = index.upsert(
            vectors=[
                {
                    "id": vector_id,
                    "values": vector_values,
                    "metadata": metadata
                }
            ]
        )
        
        logger.info(f"Vector added successfully with ID {vector_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to add vector to database: {str(e)}")
        return False

def clustering_classify(index_name="github-actions-errors", n_clusters=8, sample_size=1000):

    try:
        index = pc.Index(index_name)
        
        fetch_response = index.fetch(ids=[], limit=sample_size)
        
        if not fetch_response.vectors:
            logger.warning("No vectors found for clustering")
            return pd.DataFrame(columns=['id', 'cluster']), None
        
        vector_data = []
        vector_ids = []
        
        for vector_id, vector_info in fetch_response.vectors.items():
            vector_ids.append(vector_id)
            vector_data.append(vector_info.values)
        
        # Convert to numpy array for clustering
        vector_array = np.array(vector_data)
        
        kmeans = KMeans(n_clusters=min(n_clusters, len(vector_data)), 
                        random_state=42, 
                        n_init=10)
        
        cluster_labels = kmeans.fit_predict(vector_array)
        
        # DataFrame with results
        result_df = pd.DataFrame({
            'id': vector_ids,
            'cluster': cluster_labels
        })
        
        logger.info(f"Clustered {len(vector_data)} vectors into {n_clusters} clusters")
        return result_df, kmeans
    except Exception as e:
        logger.error(f"Error in clustering: {str(e)}")
        return pd.DataFrame(columns=['id', 'cluster']), None