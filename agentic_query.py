import os
import sys
import kuzu
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

class RichCallbackHandler(BaseCallbackHandler):
    def on_agent_action(self, action, **kwargs):
        log = action.log
        if "Thought:" in log:
            thought = log.split("Thought:")[-1].split("Action:")[0].strip()
            if thought:
                console.print(f"\n[dim italic blue]🧠 [Agent Thinking][/dim italic blue] {thought}")
        
        tool_name = action.tool
        tool_input = action.tool_input
        
        icon = "⚙️"
        if tool_name == "Search_Raw_Text":
            icon = "📚"
        elif tool_name == "Search_Fuzzy_Edges":
            icon = "🕸️"
        elif tool_name == "Search_Exact_Character_Graph":
            icon = "🎯"
        elif tool_name == "Search_RAPTOR_Summaries":
            icon = "🦅"
            
        console.print(f"[bold magenta]{icon} [{tool_name}][/bold magenta] Searching for: [cyan]{tool_input}[/cyan]")
        
    def on_tool_end(self, output, **kwargs):
        if "No " in output or "Failed" in output:
            console.print(f"[bold red]❌ Result:[/bold red] {output}")
        else:
            length = len(output)
            console.print(f"[bold green]✅ Result:[/bold green] Retrieved {length} characters of context.")
        
    def on_agent_finish(self, finish, **kwargs):
        console.print("\n")
        answer = finish.return_values.get("output", "")
        console.print(Panel(Markdown(answer), title="[bold green]Final Answer[/bold green]", border_style="green"))


# Load Env
load_dotenv()
if not os.environ.get("GOOGLE_API_KEY"):
    print("ERROR: GOOGLE_API_KEY environment variable not set. Please export it first!")
    sys.exit(1)

# Initialize Embeddings
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

# 1. Initialize Vector Index (Path A)
vectorstore = Chroma(persist_directory="./chroma_db_mahabharata", embedding_function=embeddings)
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 2. Initialize Edge Embeddings (Path B)
edges_vectorstore = Chroma(persist_directory="./chroma_db_edges", embedding_function=embeddings)
edges_retriever = edges_vectorstore.as_retriever(search_kwargs={"k": 10})

# 3. Initialize KuzuDB (Path C)
kuzu_db = kuzu.Database("./kuzu_db")
kuzu_conn = kuzu.Connection(kuzu_db)

# 4. Initialize RAPTOR Summaries (Path D)
raptor_vectorstore = Chroma(persist_directory="./chroma_db_raptor", embedding_function=embeddings)
raptor_retriever = raptor_vectorstore.as_retriever(search_kwargs={"k": 3})

# --- DEFINE TOOLS ---
def search_vector_index(query: str) -> str:
    """Searches the raw text of the Mahabharata for specific paragraphs, scenes, and descriptions."""
    docs = vector_retriever.invoke(query)
    if not docs:
        return "No paragraphs found."
    return "\n\n".join([f"[Paragraph]: {doc.page_content}" for doc in docs])

def search_edge_embeddings(query: str) -> str:
    """Searches the Knowledge Graph mathematically for conceptual or fuzzy relationships between entities."""
    docs = edges_retriever.invoke(query)
    if not docs:
        return "No edge relationships found."
    return "\n".join([doc.page_content for doc in docs])

def search_cypher_graph(character_name: str) -> str:
    """Forcefully extracts EVERY known deterministic relationship involving a specific Character's Name. Input MUST be a character name, e.g., 'Karnos'."""
    # Clean the input just in case
    char_name = character_name.strip("'").strip('"').strip().lower()
    query = f"MATCH (s:Entity)-[r:RelatedTo]->(o:Entity) WHERE toLower(s.name) CONTAINS '{char_name}' OR toLower(o.name) CONTAINS '{char_name}' RETURN s.name, r.relationship, o.name LIMIT 30"
    try:
        results = kuzu_conn.execute(query)
        cypher_facts = []
        while results.has_next():
            row = results.get_next()
            cypher_facts.append(f"[{row[0]}] --({row[1]})--> [{row[2]}]")
        if not cypher_facts:
            return f"No hard facts found for character {char_name}."
        return "\n".join(cypher_facts)
    except Exception as e:
        return f"Cypher Execution Failed: {e}"

def search_raptor_summaries(query: str) -> str:
    """Searches High-Level hierarchical summaries of the epic. Use this for broad, thematic, or global reasoning questions (e.g. 'What caused the war?', 'What is Dharma?')."""
    docs = raptor_retriever.invoke(query)
    if not docs:
        return "No global summaries found."
    return "\n\n".join([f"[RAPTOR Summary]: {doc.page_content}" for doc in docs])

tools = [
    Tool(
        name="Search_Raw_Text",
        func=search_vector_index,
        description="Searches raw text paragraphs. Use natural language sentences (e.g., 'How did ENTITY_DRO6 die?'). Do NOT use keyword mashups. Do NOT use real names."
    ),
    Tool(
        name="Search_Fuzzy_Edges",
        func=search_edge_embeddings,
        description="Searches graph edges using conceptual meaning. Use to find actions like 'who killed X' or 'who taught Y' when you don't know the character names."
    ),
    Tool(
        name="Search_Exact_Character_Graph",
        func=search_cypher_graph,
        description="Extracts all graph edges for a SPECIFIC character. Input must ONLY be a Character Name (e.g. 'ENTITY_ARJ7'). Highly accurate for character logic."
    ),
    Tool(
        name="Search_RAPTOR_Summaries",
        func=search_raptor_summaries,
        description="Searches global summaries. Use for broad, thematic, or philosophical questions spanning multiple chapters."
    )
]

# --- DEFINE AGENT ---
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0)

# ReAct Prompt
template = '''Answer the following questions as best you can. You are an expert on the Mahabharata. You have access to the following tools:

{tools}

CRITICAL RULE 1 (Blind Searching): You must ONLY use the provided ENTITY_XXX, FACTION_XXX, or LOCATION_XXX IDs in your tool inputs. Do NOT attempt to guess their real names or translate them back into English. For example, if you see ENTITY_DRO6, query using ENTITY_DRO6.
CRITICAL RULE 2 (Anti-Hallucination): In your Final Answer, you are STRICTLY FORBIDDEN from mentioning any facts, storylines, or events that were not explicitly stated in the 'Observation' blocks. Do not use your pre-trained knowledge to fill in gaps. If the text does not say why someone did something, do not add it!
CRITICAL RULE 3 (Scrubbed Databases): The underlying databases have been COMPLETELY SCRUBBED of all real character names (like Drona, Arjuna, Bhima, etc). If you attempt to search for real names, you will get ZERO results. You MUST search using ONLY the provided IDs. Do not attempt to reverse-engineer or use canonical names in your searches!
CRITICAL RULE 4 (Vector Search Strategy): When using Search_Raw_Text, use full, natural language sentences (e.g., 'How did ENTITY_DRO6 die?'). Do NOT use boolean keywords (e.g., 'ENTITY_DRO6 killed sword').

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do, what tools to use, and whether you need to chain searches.
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times until you have enough evidence)
Thought: I now know the final answer based STRICTLY on the Observations.
Final Answer: the final synthesized answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}'''

prompt = PromptTemplate.from_template(template)

agent = create_react_agent(llm, tools, prompt)

# We use a custom Rich callback handler to beautifully format the output
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=False, 
    handle_parsing_errors=True,
    max_iterations=30,
    callbacks=[RichCallbackHandler()]
)

def run_agentic_loop():
    print("\n--- AGENTIC RAG SYSTEM READY ---")
    print("The AI will now autonomously decide which databases to query, investigate leads, and stream its thoughts to you.")
    
    while True:
        try:
            query = input("\nAsk a multi-hop or global question about the epic: ")
        except EOFError:
            break
            
        if query.lower() in ['exit', 'quit']:
            break
            
        print("\n===========================================")
        print(f"USER: {query}")
        print("===========================================\n")
        try:
            # Execute the agent and stream thoughts to terminal
            agent_executor.invoke({"input": query})
        except Exception as e:
            print(f"\nAgent failed: {e}")
            
if __name__ == "__main__":
    run_agentic_loop()
