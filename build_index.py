import os
import warnings
import shutil

warnings.filterwarnings("ignore")

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.embeddings import Embeddings
import time
from dotenv import load_dotenv

DB_DIR = "./chroma_db_mahabharata"

class RetryEmbeddings(Embeddings):
    def __init__(self, model_name="gemini-embedding-2"):
        self.emb = GoogleGenerativeAIEmbeddings(model=model_name)
        
    def embed_documents(self, texts):
        while True:
            try:
                return self.emb.embed_documents(texts)
            except Exception as e:
                print(f"    [Embedding Rate Limit] Sleeping for 10s... ({e})")
                time.sleep(10)
                
    def embed_query(self, text):
        while True:
            try:
                return self.emb.embed_query(text)
            except Exception as e:
                print(f"    [Embedding Rate Limit] Sleeping for 10s... ({e})")
                time.sleep(10)

def build_index():
    load_dotenv()
    if not os.environ.get("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY environment variable not set. Please export it first!")
        return

    print(f"0. Cleaning up old database at {DB_DIR}...")
    shutil.rmtree(DB_DIR, ignore_errors=True)
    
    print("1. Initializing Embedding model from Google API (gemini-embedding-2)...")
    embeddings = RetryEmbeddings(model_name="gemini-embedding-2")
    
    print("2. Loading documents from 'data/' directory...")
    # Load our specific swapped text file
    loader = DirectoryLoader('./data', glob="mahabharata_swapped.txt", loader_cls=TextLoader)
    docs = loader.load()
    
    # We will use slightly larger chunks for literature to preserve narrative context
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)
    print(f"Loaded and split the Mahabharata into {len(splits)} narrative chunks.")
    
    print("3. Embedding chunks and saving to ChromaDB in batches to prevent API timeouts...")
    vectorstore = Chroma(embedding_function=embeddings, persist_directory=DB_DIR)
    
    batch_size = 50
    total_batches = (len(splits) + batch_size - 1) // batch_size
    
    for i in range(0, len(splits), batch_size):
        batch = splits[i : i + batch_size]
        print(f"   Processing batch {i // batch_size + 1} of {total_batches}...")
        vectorstore.add_documents(batch)
    
    print("\n--- Indexing Complete! You can now run query.py ---")

if __name__ == "__main__":
    build_index()
