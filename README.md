# Mahabharata Hybrid RAG Knowledge Base

This project implements an enterprise-grade **Hybrid Retrieval-Augmented Generation (RAG)** architecture to process, index, and query the entire 750,000-character Mahabharata epic (C. Rajagopalachari translation). 

By combining the semantic storytelling context of a Vector Database with the undeniable factual logic of a Knowledge Graph, this system eliminates LLM hallucinations and provides highly accurate, context-rich answers to complex questions about the epic.

## Architecture

The system is split into two parallel retrieval pipelines that converge into a final master synthesis:

1. **Semantic Vector Search (ChromaDB)**
   - Text is chopped into small chunks and mathematically embedded into a local vector space.
   - Ideal for retrieving rich story context, descriptive prose, and general thematic matching.
   - **Local Pivot**: Upgraded to use 100% local, uncensored embeddings via Ollama (`mxbai-embed-large`) to bypass cloud rate limits, with a seamless toggle (`USE_LOCAL_EMBEDDINGS`) for backward compatibility.

2. **GraphRAG (KuzuDB)**
   - Text is processed by a frontier LLM to extract complex relationships across an advanced ontology.
   - The graph tracks Nodes dynamically categorized as `Character`, `Location`, `Concept`, `Weapon`, or `Event`.
   - **Edge Embeddings**: During extraction, every edge string (e.g., `[Subject] --(action)--> [Object]`) is simultaneously embedded into a parallel ChromaDB (`chroma_db_edges`). This completely eliminates Cypher's brittle string-matching flaws and allows fuzzy semantic search directly on Graph relationships!

3. **RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval)**
   - Text chunks are semantically clustered using UMAP dimensionality reduction and Gaussian Mixture Models (GMM).
   - Clusters are recursively summarized by an LLM up to a depth of 3, allowing the system to answer sweeping thematic or multi-hop questions by retrieving high-level summaries instead of missing context scattered across isolated chunks.

4. **Tri-brid Synthesis (The Master Cascade)**
   - The final query engine (`hybrid_query.py`) utilizes a highly coveted Tri-brid Architecture:
     - **Path A (The Poet)**: Searches the raw paragraph vector database for thematic storytelling.
     - **Path B (The Intuitive Historian)**: Searches the Edge Embeddings mathematically for conceptual or fuzzy relationship matches.
     - **Path C (The Rigid Historian)**: A generative LLM writes a rigid Kuzu Cypher query that forcefully pulls *all* edges connected to the requested characters, ignoring the relationship verb completely to prevent extraction loss.
   - It synthesizes all three data streams into a single Master Prompt for the final LLM to generate an incredibly accurate answer.

## Technologies Used

- **LangChain**: The core orchestration framework tying the databases, models, and fallback cascades together.
- **Ollama**: Powers the 100% local, uncensored embedding infrastructure (`mxbai-embed-large`).
- **KuzuDB**: A hyper-fast, embeddable graph database used to store character interaction edges.
- **ChromaDB**: The local vector database used to store semantic text embeddings AND Edge Embeddings.
- **Google Gemini / Gemma APIs**: Powers the generative reasoning steps via the `langchain-google-genai` integration (Graph Extraction, Cypher Fallback, and Final Synthesis).
- **Pydantic**: Enforces strict JSON schema validation for the GraphRAG extraction via LangChain's `with_structured_output`, ensuring the LLM perfectly maps its findings to the Kuzu schema.
- **BM25 Keyword Search**: A sparse retrieval method used for exact keyword and ID matching.

## Anti-Bleeding Strategy (Cryptographic Mappings)
One of the biggest challenges with LLMs in RAG architectures for famous texts (like the Mahabharata) is **pre-training bleed** — where the model ignores the retrieved context and answers from its training data. 
To completely eliminate this:
1. **Total Identity Wipe**: `scripts/download_and_prep_data.py` uses aggressive regex to swap over 50 canonical characters, gods, and locations with meaningless hashes (e.g., Arjuna -> `ENTITY_ARJ7`, Drona -> `ENTITY_DRO6`).
2. **Semantic Anchors Removed**: Even minor characters and spouses (like Abhimanyu or Subhadra) are swapped, ensuring the LLM cannot "triangulate" the identities through relationships.
3. **Strict Agent Guardrails**: The ReAct prompt in `agentic_query.py` explicitly forbids the LLM from trying to map `ENTITY_XXX` IDs back to real names, forcing it to generate its answers *purely* from the observed context.
## Resilience (Cascade Failover)
To rapidly process the entire 750,000-character epic without spending money on API costs, this project utilizes a custom **LangChain Fallback Cascade**. If a model hits a Free Tier rate limit (HTTP 429), the architecture instantly catches the error and seamlessly routes the request to the next available model in a predefined priority list (e.g., `gemini-3.5-flash-lite` -> `gemini-3.1-flash-lite` -> `gemma-4-31b`).

## Project Files

### Data Preparation
- `scripts/download_and_prep_data.py`: Downloads the raw text, sanitizes OCR errors, and standardizes character aliases across the entire epic using regex and **Cryptographic ID Mapping** (e.g. replacing 'Arjuna' with 'ENTITY_ARJ7') to completely blind the LLM from its pre-training bias, ensuring answers are purely derived from the retrieved RAG context.

### Database Construction
- `scripts/build_index.py`: Chunks the text and embeds it into the Chroma Vector Database.
- `scripts/build_graph.py`: Batches the text and uses Gemini to extract relationships into the Kuzu Graph Database.
- `scripts/build_raptor.py`: Runs UMAP/GMM clustering and LLM summarization to build the hierarchical RAPTOR index.

### Query Engines
- `query_graph.py`: A pure GraphRAG engine that extracts target entities and runs Cypher queries.
- `hybrid_query.py`: An engine that combines Vector and Graph databases to generate the perfect answer using dynamic Text-to-Cypher logic.
- `agentic_query.py`: An autonomous agent loop that decides which tools to query (Raw Text, Fuzzy Edges, RAPTOR Summaries) and when to answer the user's question, displaying its "thoughts" to the user along the way.

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/venkteshgm/rag-knowledge-base.git
   cd rag-knowledge-base
   ```
2. Create a `.env` file in the root directory and add your Google API key:
   ```env
   GOOGLE_API_KEY="your_google_api_key_here"
   ```
3. Run the automated setup script to install dependencies, clean data, and build all databases:
   ```bash
   bash setup.sh
   ```
4. Query the epic (Agentic Mode):
   ```bash
   python agentic_query.py
   ```
