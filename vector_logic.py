import openai
import tiktoken
import numpy as np
import pandas as pd
from ast import literal_eval
from pinecone import Pinecone
import os
from sklearn.cluster import KMeans
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.environ.get("OPENAI_KEY")
client = openai

pc = Pinecone(api_key=os.environ.get("PINECONE_KEY")
    )
def vector_embeddings(input):
    """Turns a string into vector"""
    response = client.embeddings.create(
    input=input,
    model="text-embedding-3-small"
)
    return response.data[0].embedding

def fix_tokens(string):
    """If string has too many tokens then it makes it shorter it"""
    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "system",
        "content": "You must reduce the size of this string down to a MAXIMUM of 1536 tokens keep all valueble infomation"
    }, {
        "role": "user",
        "content": string}])
    return completion.choices[0].message.content


def token_checker(string, encoding_name):
    """Changes the length of tokens to fit in vector"""
    DIMENSIONS = 1536
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(string)
    
    if len(tokens) > DIMENSIONS:
        return fix_tokens(string)
    return string


def clustering_classify(index_name="example-index1", n_clusters=8, sample_size=1000):
    """Classifys each error for supabase"""
    index = pc.Index(index_name)
    
    fetch_response = index.fetch(ids=[], limit=sample_size)
    
    if not fetch_response.vectors:
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
    
    return result_df, kmeans

def predict_vector_cluster(vector=None, index_name="example-index1", n_clusters=8, sample_size=1000):
    """Predicts what the new vector would fit into"""
    if vector is None:
        return False
    
    _, kmeans_model = clustering_classify(index_name, n_clusters, sample_size)
    
    if kmeans_model is None:
        return False
        
    # Reshape for single sample prediction
    vector_array = np.array(vector).reshape(1, -1)
    
    # Predict the cluster
    cluster = kmeans_model.predict(vector_array)[0]
    
    return int(cluster)

def distance(vector, index_name="example-index1"):
    """Find the diffrence between the new vector and the old vectors"""
    index = pc.Index(index_name)
    results = index.query(
        vector=vector,
        filter = {
        "genre": "errors"
        },
        top_k=3,
        include_values=True,
        include_metadata=True
    )
    
    matches = results.matches
    
    retrieved_vectors = []
    for match in matches:
        retrieved_vectors.append({
            "id": match.id,
            "score": match.score,
            "values": match.values,
            "metadata": match.metadata
        })
    
    return retrieved_vectors

def add_vector(index_name="example-index1", vector_id="id123", vector_values=None, metadata={}):
    """add the vector to the pinecone """
    index = pc.Index(index_name)
    index.upsert(vectors=[
        {"id": vector_id, "values": vector_values, "metadata": metadata}
    ])