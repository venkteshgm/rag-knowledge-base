import os
import kuzu
import warnings
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import time
import json

CHROMA_DB_DIR = "./chroma_db_mahabharata"
KUZU_DB_DIR = "./kuzu_db"
EDGES_DB_DIR = "./chroma_db_edges"
USE_LOCAL_EMBEDDINGS = True

class CypherQuery(BaseModel):
    query: str = Field(description="A valid Kuzu Cypher query to retrieve facts answering the user's question.")

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

def hybrid_query():
    load_dotenv()
    if not os.environ.get("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY environment variable not set. Please export it first!")
        return

    print("1. Initializing Local Vector Database (Chroma)...")
    if not os.path.exists(CHROMA_DB_DIR):
        print(f"Error: Vector DB {CHROMA_DB_DIR} not found.")
        return
        
    if USE_LOCAL_EMBEDDINGS:
        embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    else:
        embeddings = RetryEmbeddings(model_name="gemini-embedding-2")
        
    vectorstore = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    print("2. Initializing Local Edge Database (Chroma)...")
    if not os.path.exists(EDGES_DB_DIR):
        print(f"Error: Edge DB {EDGES_DB_DIR} not found.")
        return
    edges_vectorstore = Chroma(persist_directory=EDGES_DB_DIR, embedding_function=embeddings)
    edges_retriever = edges_vectorstore.as_retriever(search_kwargs={"k": 15})

    print("2.5 Initializing Kuzu DB for Cypher Fallback...")
    if not os.path.exists(KUZU_DB_DIR):
        print(f"Error: Kuzu DB {KUZU_DB_DIR} not found.")
        return
    kuzu_db = kuzu.Database(KUZU_DB_DIR)
    kuzu_conn = kuzu.Connection(kuzu_db)

    print("3. Initializing Cloud LLM Cascade (Gemini/Gemma) for Final Synthesis...")
    models_to_try = [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemma-4-31b",
        "gemma-4-26b"
    ]
    
    # Text Generator Cascade
    generator_llms = []
    for model_name in models_to_try:
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0, max_retries=0)
        generator_llms.append(llm)
    generator_chain = generator_llms[0].with_fallbacks(generator_llms[1:])

    print("\n--- HYBRID RAG SYSTEM READY. Type 'exit' to quit. ---")
    
    while True:
        try:
            query = input("\nAsk a question about the epic: ")
        except EOFError:
            break
            
        if query.lower() in ['exit', 'quit']:
            break
            
        print("\nThinking...")
        
        # --- PATH A: VECTOR RETRIEVAL ---
        print("  -> Searching Vector Space for Semantic Context...")
        docs = vector_retriever.invoke(query)
        vector_context = "\n\n".join([f"[Paragraph {i+1}]: {doc.page_content}" for i, doc in enumerate(docs)])
        
        # --- PATH B: EDGE RETRIEVAL (VECTOR-GRAPH HYBRID) ---
        print("  -> Searching Graph Edges via Semantic Math...")
        edge_docs = edges_retriever.invoke(query)
        graph_facts = "\n".join([doc.page_content for doc in edge_docs])
        if graph_facts:
            print(f"     Found {len(edge_docs)} relevant semantic edges in the Knowledge Graph.")

        # --- PATH C: CYPHER FALLBACK (DETERMINISTIC EXTRACT) ---
        print("  -> Searching Graph via Deterministic Cypher...")
        cypher_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI that writes KuzuDB Cypher queries. The graph has ONE node table: Entity (name STRING, label STRING) and ONE relationship table: RelatedTo. "
                       "RULE: NEVER filter by the relationship verb. ONLY filter by Character names using CONTAINS. "
                       "Return ONLY the raw Cypher query string and nothing else, no markdown formatting. "
                       "Example: MATCH (s:Entity)-[r:RelatedTo]->(o:Entity) WHERE toLower(s.name) CONTAINS 'parasurama' OR toLower(o.name) CONTAINS 'parasurama' RETURN s.name, r.relationship, o.name LIMIT 20"),
            ("human", "Question: {input}")
        ])
        cypher_chain = cypher_prompt | generator_chain | StrOutputParser()
        try:
            cypher_query_str = cypher_chain.invoke({"input": query}).strip().strip("`").replace("cypher\n", "")
            if cypher_query_str.lower().startswith("match"):
                print(f"     Executing Cypher: {cypher_query_str}")
                results = kuzu_conn.execute(cypher_query_str)
                cypher_facts_list = []
                while results.has_next():
                    row = results.get_next()
                    cypher_facts_list.append(f"[{row[0]}] --({row[1]})--> [{row[2]}]")
                if cypher_facts_list:
                    print(f"     Found {len(cypher_facts_list)} exact Cypher edges.")
                    # Combine with semantic edge facts
                    if graph_facts:
                        graph_facts += "\n" + "\n".join(cypher_facts_list)
                    else:
                        graph_facts = "\n".join(cypher_facts_list)
        except Exception as e:
            print(f"     Cypher Fallback failed: {e}")

        # --- STEP 3: MASTER SYNTHESIS ---
        print("  -> Synthesizing Hybrid Answer...")
        
        system_prompt = (
            "You are an expert on the Mahabharata epic. "
            "Answer the user's question accurately using ONLY the context provided below.\n\n"
            "=== HARD GRAPH FACTS ===\n"
            "Use these undeniable character interactions as the bedrock of your logic. Do not contradict them.\n"
            "{graph_facts}\n\n"
            "=== SEMANTIC STORY CONTEXT ===\n"
            "Use these paragraphs to provide rich descriptive details and storytelling to your answer.\n"
            "{vector_context}\n"
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}")
        ])
        
        final_chain = prompt | generator_chain | StrOutputParser()
        
        try:
            response = final_chain.invoke({
                "graph_facts": graph_facts if graph_facts else "No concrete graph edges found.",
                "vector_context": vector_context if vector_context else "No semantic context found.",
                "input": query
            })
            print("\n=== HYBRID ANSWER ===")
            print(response)
            print("=====================")
        except Exception as e:
            print(f"\nFailed to generate answer: {e}")

if __name__ == "__main__":
    hybrid_query()
