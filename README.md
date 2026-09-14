# Mahabharata Hybrid RAG Knowledge Base

This project implements an enterprise-grade **Hybrid Retrieval-Augmented Generation (RAG)** architecture to process, index, and query the entire 750,000-character Mahabharata epic (C. Rajagopalachari translation). 

By combining the semantic storytelling context of a Vector Database with the undeniable factual logic of a Knowledge Graph, this system eliminates LLM hallucinations and provides highly accurate, context-rich answers to complex questions about the epic.

## Architecture

The system is split into two parallel retrieval pipelines that converge into a final master synthesis:

1. **Semantic Vector Search (ChromaDB)**
   - Text is chopped into small chunks and mathematically embedded into a local vector space.
   - Ideal for retrieving rich story context, descriptive prose, and general thematic matching.
   - Employs a *Multi-Query Retriever* pattern to generate variations of the user's question to overcome distance-based similarity limitations.

2. **GraphRAG (KuzuDB)**
   - Text is processed in massive 15,000-character batches by a frontier LLM to extract concrete noun relationships (e.g., `[Arjunos] --(killed)--> [Karnos]`).
   - These facts are stored as explicit Nodes and Edges in a local Knowledge Graph.
   - Completely immune to "Context Fragmentation" and guarantees factual accuracy.

3. **Hybrid Synthesis**
   - The final query engine (`hybrid_query.py`) simultaneously searches ChromaDB for context and KuzuDB for hard facts.
   - It synthesizes both data streams into a single Master Prompt, allowing the generation LLM to anchor its logic in the graph while drawing descriptive flavor from the vector chunks.

## Technologies Used

- **LangChain**: The core orchestration framework tying the databases, models, and fallback cascades together.
- **KuzuDB**: A hyper-fast, embeddable graph database used to store character interaction edges.
- **ChromaDB**: The local vector database used to store semantic text embeddings.
- **Ollama**: Used to run local, privacy-first embedding models (`nomic-embed-text`).
- **Google Gemini / Gemma APIs**: Powers the heavy lifting (Graph Extraction and Final Synthesis) via the `langchain-google-genai` integration.
- **Pydantic**: Enforces strict JSON schema validation for the GraphRAG extraction via LangChain's `with_structured_output`, ensuring the LLM perfectly maps its findings to the Kuzu schema.

## Resilience (Cascade Failover)
To rapidly process the entire 750,000-character epic without spending money on API costs, this project utilizes a custom **LangChain Fallback Cascade**. If a model hits a Free Tier rate limit (HTTP 429), the architecture instantly catches the error and seamlessly routes the request to the next available model in a predefined priority list (e.g., `gemini-3.5-flash-lite` -> `gemini-3.1-flash-lite` -> `gemma-4-31b`).

## Project Files

### Data Preparation
- `scripts/download_and_prep_data.py`: Downloads the raw text, sanitizes OCR errors, and standardizes character aliases across the entire epic using regex.

### Database Construction
- `build_index.py`: Chunks the text and embeds it into the Chroma Vector Database.
- `build_graph.py`: Batches the text and uses Gemini to extract relationships into the Kuzu Graph Database.

### Query Engines
- `query.py`: A pure Vector RAG engine using Ollama and a Multi-Query Retriever.
- `query_graph.py`: A pure GraphRAG engine that extracts target entities and runs Cypher queries.
- `hybrid_query.py`: The ultimate engine that combines both Vector and Graph databases to generate the perfect answer.

## Setup & Execution

1. Ensure Ollama is installed and running locally with the following models:
   ```bash
   ollama pull llama3.2
   ollama pull nomic-embed-text
   ```
2. Install the required python dependencies:
   ```bash
   pip install langchain langchain-chroma langchain-ollama langchain-google-genai pydantic kuzu python-dotenv
   ```
3. Create a `.env` file in the root directory and add your Google API key:
   ```env
   GOOGLE_API_KEY="your_api_key_here"
   ```
4. Run the data prep and build scripts:
   ```bash
   python scripts/download_and_prep_data.py
   python build_index.py
   python build_graph.py
   ```
5. Query the epic:
   ```bash
   python hybrid_query.py
   ```
