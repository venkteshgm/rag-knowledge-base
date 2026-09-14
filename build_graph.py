import kuzu
import os
import shutil
import time
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

DB_DIR = "./kuzu_db"

class Node(BaseModel):
    name: str = Field(description="The unique name of the entity")
    label: str = Field(description="The category: Character, Location, Concept, Weapon, or Event")

class Edge(BaseModel):
    source: str = Field(description="The name of the source node")
    target: str = Field(description="The name of the target node")
    relationship: str = Field(description="The relationship, e.g. 'killed', 'located_in', 'influenced_by'")

class GraphExtraction(BaseModel):
    nodes: List[Node] = Field(description="All distinct entities mentioned in the text")
    edges: List[Edge] = Field(description="All relationships between the extracted nodes")

def build_graph():
    load_dotenv()
    if not os.environ.get("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY environment variable not set. Please export it first!")
        return

    if os.path.exists(DB_DIR):
        if os.path.isdir(DB_DIR):
            shutil.rmtree(DB_DIR)
        else:
            os.remove(DB_DIR)
        
    print("1. Initializing KuzuDB...")
    db = kuzu.Database(DB_DIR)
    conn = kuzu.Connection(db)
    
    print("2. Creating Graph Schema...")
    conn.execute("CREATE NODE TABLE Entity (name STRING, label STRING, PRIMARY KEY (name))")
    conn.execute("CREATE REL TABLE RelatedTo (FROM Entity TO Entity, relationship STRING)")
    
    print("3. Loading the FULL Mahabharata...")
    with open("data/mahabharata_swapped.txt", "r", encoding="utf-8") as f:
        text = f.read()
        
    print(f"Total size: {len(text)} chars")
        
    splitter = RecursiveCharacterTextSplitter(chunk_size=15000, chunk_overlap=500)
    chunks = splitter.split_text(text)
    
    print(f"Generated {len(chunks)} chunks. Processing with Model Cascade... (This will take a few minutes)")
    
    # Initialize Model Fallback Cascade
    models_to_try = [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemma-4-31b",
        "gemma-4-26b"
    ]
    
    structured_llms = []
    for model_name in models_to_try:
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0, max_retries=0)
        structured_llms.append(llm.with_structured_output(GraphExtraction))
        
    structured_llm = structured_llms[0].with_fallbacks(structured_llms[1:])
    
    inserted_chars = set()
    start_time = time.time()
    
    # Process ALL chunks for the full epic
    for i, chunk in enumerate(chunks):
        print(f"  Processing chunk {i+1}/{len(chunks)}...")
        try:
            # We don't need a text prompt anymore, just pass the chunk directly
            # The structure and schema description is already bound to the API request
            extraction = structured_llm.invoke(f"Extract relationships from this text: {chunk}")
            
            for node in extraction.nodes:
                n = node.name.strip().title()
                l = node.label.strip().title()
                if len(n) > 20 or not n:
                    continue
                if n not in inserted_chars:
                    conn.execute("CREATE (:Entity {name: $name, label: $label})", parameters={"name": n, "label": l})
                    inserted_chars.add(n)
            
            for rel in extraction.edges:
                sub = rel.source.strip().title()
                obj = rel.target.strip().title()
                act = rel.relationship.strip().lower()
                
                if len(sub) > 20 or len(obj) > 20 or not sub or not obj:
                    continue
                    
                # In case an edge references a node that wasn't properly listed in nodes
                if sub not in inserted_chars:
                    conn.execute("CREATE (:Entity {name: $name, label: $label})", parameters={"name": sub, "label": "Unknown"})
                    inserted_chars.add(sub)
                if obj not in inserted_chars:
                    conn.execute("CREATE (:Entity {name: $name, label: $label})", parameters={"name": obj, "label": "Unknown"})
                    inserted_chars.add(obj)
                    
                conn.execute(
                    "MATCH (s:Entity {name: $sub}), (o:Entity {name: $obj}) "
                    "CREATE (s)-[:RelatedTo {relationship: $act}]->(o)",
                    parameters={"sub": sub, "obj": obj, "act": act}
                )
                print(f"    --> Graph Edge: [{sub}] --({act})--> [{obj}]")
                
        except Exception as e:
            print(f"    Failed to process chunk: {e}")

    end_time = time.time()
    elapsed = end_time - start_time
    print(f"\nGraph Indexing Complete! Nodes and edges successfully saved to KuzuDB.")
    print(f"Total time to build graph with Gemini: {elapsed:.2f} seconds.")

if __name__ == "__main__":
    build_graph()
