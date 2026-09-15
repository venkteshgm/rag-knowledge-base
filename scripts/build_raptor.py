import os
import time
import numpy as np
import umap
from sklearn.mixture import GaussianMixture
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document

CHROMA_DB_DIR = "./chroma_db_mahabharata"
RAPTOR_DB_DIR = "./chroma_db_raptor"

def get_optimal_clusters(embeddings, max_clusters=50):
    """Find optimal number of clusters using BIC"""
    print("  -> Finding optimal cluster count using BIC...")
    max_clusters = min(max_clusters, len(embeddings))
    n_components = np.arange(1, max_clusters, min(5, max_clusters//5 + 1))
    models = [GaussianMixture(n, covariance_type='full', random_state=42).fit(embeddings)
              for n in n_components]
    bics = [m.bic(embeddings) for m in models]
    optimal_n = n_components[np.argmin(bics)]
    print(f"  -> Optimal clusters found: {optimal_n}")
    return optimal_n

def build_raptor():
    load_dotenv()
    if not os.environ.get("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY environment variable not set. Please export it first!")
        return

    print("1. Loading raw vectors from ChromaDB...")
    embeddings_model = OllamaEmbeddings(model="mxbai-embed-large")
    vectorstore = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings_model)
    
    # Retrieve all documents and embeddings
    # Note: Chroma get() without args returns all items
    results = vectorstore.get(include=['embeddings', 'documents'])
    
    docs = results['documents']
    embeddings = np.array(results['embeddings'])
    
    if not docs or len(docs) == 0:
        print("Error: No documents found in ChromaDB.")
        return
        
    print(f"  -> Successfully loaded {len(docs)} chunks and embeddings.")

    print("\n2. Dimensionality Reduction (UMAP)...")
    # Reduce dimensions for better clustering
    n_neighbors = min(15, len(embeddings) - 1)
    reducer = umap.UMAP(
        n_neighbors=n_neighbors,
        n_components=5, # Reduce to 5D for clustering
        metric='cosine',
        random_state=42
    )
    reduced_embeddings = reducer.fit_transform(embeddings)
    print("  -> Reduced embeddings to 5 dimensions.")

    print("\n3. Clustering (GMM)...")
    n_clusters = get_optimal_clusters(reduced_embeddings, max_clusters=int(len(embeddings)*0.1) + 5)
    gmm = GaussianMixture(n_components=n_clusters, covariance_type='full', random_state=42)
    labels = gmm.fit_predict(reduced_embeddings)
    
    # Group documents by cluster
    clusters = {i: [] for i in range(n_clusters)}
    for doc_idx, label in enumerate(labels):
        clusters[label].append(docs[doc_idx])
        
    print(f"  -> Clustered {len(docs)} chunks into {n_clusters} clusters.")

    print("\n4. Generating Summaries (LLM)...")
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0)
    summaries = []
    
    for cluster_id, cluster_docs in clusters.items():
        print(f"  -> Summarizing Cluster {cluster_id+1}/{n_clusters} ({len(cluster_docs)} chunks)...")
        
        # Combine docs into one string, truncating if necessary to save tokens
        combined_text = "\n\n".join(cluster_docs)
        # Limit to roughly 50,000 characters just in case it's huge, though flash handles 1M tokens
        combined_text = combined_text[:100000] 
        
        prompt = (
            "You are an expert scholar of the Mahabharata. "
            "The following texts are related excerpts grouped together by an AI clustering algorithm. "
            "Write a highly detailed, comprehensive summary of the events, themes, and character interactions in these texts. "
            "Your summary should be 1-3 paragraphs long and capture the overarching narrative of this specific group of texts.\n\n"
            f"TEXTS:\n{combined_text}"
        )
        
        try:
            summary = llm.invoke(prompt).content
            # Store with metadata indicating it's a RAPTOR summary level 1
            summaries.append(Document(page_content=summary, metadata={"raptor_level": 1, "cluster_id": cluster_id}))
            time.sleep(1) # Slight pause to prevent rate limiting
        except Exception as e:
            print(f"     Failed to summarize cluster {cluster_id}: {e}")

    print("\n5. Saving RAPTOR Summaries to new Vector DB...")
    raptor_vectorstore = Chroma.from_documents(
        documents=summaries,
        embedding=embeddings_model,
        persist_directory=RAPTOR_DB_DIR
    )
    print(f"  -> Saved {len(summaries)} RAPTOR summaries to {RAPTOR_DB_DIR}.")
    print("\n--- RAPTOR Indexing Complete! ---")

if __name__ == "__main__":
    build_raptor()
