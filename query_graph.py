import kuzu
import os
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

DB_DIR = "./kuzu_db"

class TargetEntity(BaseModel):
    entity: str = Field(description="The main character entity from the question")

def query_graph():
    load_dotenv()
    if not os.environ.get("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY environment variable not set. Please export it first!")
        return

    print("1. Initializing models...")
    models_to_try = [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemma-4-31b",
        "gemma-4-26b"
    ]
    
    structured_llms = []
    for model_name in models_to_try:
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0, max_retries=0)
        structured_llms.append(llm.with_structured_output(TargetEntity))
        
    structured_llm = structured_llms[0].with_fallbacks(structured_llms[1:])
    
    print("2. Connecting to Kuzu Knowledge Graph...")
    try:
        db = kuzu.Database(DB_DIR)
        conn = kuzu.Connection(db)
    except Exception as e:
        print("Could not connect to KuzuDB. Has it been built yet?", e)
        return
        
    print("\n--- GraphRAG System Ready. Type 'exit' to quit. ---")
    
    while True:
        try:
            query = input("\nAsk a question about the story: ")
        except EOFError:
            break
            
        if query.lower() in ['exit', 'quit']:
            break
            
        print("\nThinking (Extracting Entities)...")
        try:
            extraction = structured_llm.invoke(f"Extract the main character entity from this question: {query}")
            target_entity = extraction.entity.strip().title()
        except Exception as e:
            print("Failed to extract entity:", e)
            continue
        
        if not target_entity:
            print("Could not determine the target entity.")
            continue
            
        print(f"Target Entity Identified: [{target_entity}]")
        print("Querying Knowledge Graph for relationships...")
        
        cypher = '''
        MATCH (s:Character)-[r:InteractedWith]->(o:Character)
        WHERE s.name = $target OR o.name = $target
        RETURN s.name, r.action, o.name
        '''
        
        try:
            results = conn.execute(cypher, parameters={"target": target_entity})
            facts = []
            while results.has_next():
                row = results.get_next()
                facts.append(f"[{row[0]}] --({row[1]})--> [{row[2]}]")
                
            if not facts:
                print("No concrete facts found in the Knowledge Graph for this entity.")
                continue
                
            print("\n=== CONCRETE FACTS RETRIEVED ===")
            for f in facts:
                print(f)
            print("==================================")
            
        except Exception as e:
            print(f"Graph query failed: {e}")

if __name__ == "__main__":
    query_graph()
