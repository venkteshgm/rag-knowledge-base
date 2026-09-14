import os
import kuzu
import warnings
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

warnings.filterwarnings("ignore")

CHROMA_DB_DIR = "./chroma_db_mahabharata"
KUZU_DB_DIR = "./kuzu_db"

class TargetEntity(BaseModel):
    entity: str = Field(description="The main character entity from the question")

def hybrid_query():
    load_dotenv()
    if not os.environ.get("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY environment variable not set. Please export it first!")
        return

    print("1. Initializing Local Vector Database (Chroma + Nomic)...")
    if not os.path.exists(CHROMA_DB_DIR):
        print(f"Error: Vector DB {CHROMA_DB_DIR} not found.")
        return
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    print("2. Initializing Local Graph Database (Kuzu)...")
    if not os.path.exists(KUZU_DB_DIR):
        print(f"Error: Graph DB {KUZU_DB_DIR} not found.")
        return
    kuzu_db = kuzu.Database(KUZU_DB_DIR)
    kuzu_conn = kuzu.Connection(kuzu_db)

    print("3. Initializing Cloud LLM Cascade (Gemini/Gemma)...")
    models_to_try = [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemma-4-31b",
        "gemma-4-26b"
    ]
    
    # 1. Structured Extractor Cascade
    structured_llms = []
    for model_name in models_to_try:
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0, max_retries=0)
        structured_llms.append(llm.with_structured_output(TargetEntity))
    extractor_chain = structured_llms[0].with_fallbacks(structured_llms[1:])
    
    # 2. Text Generator Cascade
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
        
        # --- PATH B: GRAPH RETRIEVAL ---
        print("  -> Extracting Entities and Searching Knowledge Graph...")
        graph_facts = ""
        try:
            extraction = extractor_chain.invoke(f"Extract the main character entity from this question: {query}")
            target_entity = extraction.entity.strip().title()
            
            if target_entity:
                print(f"     Found target entity: [{target_entity}]")
                cypher = '''
                MATCH (s:Character)-[r:InteractedWith]->(o:Character)
                WHERE s.name = $target OR o.name = $target
                RETURN s.name, r.action, o.name
                '''
                results = kuzu_conn.execute(cypher, parameters={"target": target_entity})
                facts = []
                while results.has_next():
                    row = results.get_next()
                    facts.append(f"[{row[0]}] --({row[1]})--> [{row[2]}]")
                
                if facts:
                    graph_facts = "\n".join(facts)
        except Exception as e:
            print(f"     Failed to query graph: {e}")

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
