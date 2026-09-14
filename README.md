# Mahabharata Hybrid RAG Knowledge Base

This project implements an enterprise-grade **Hybrid Retrieval-Augmented Generation (RAG)** architecture to process, index, and query the entire 750,000-character Mahabharata epic (C. Rajagopalachari translation). 

By combining the semantic storytelling context of a Vector Database with the undeniable factual logic of a Knowledge Graph, this system eliminates LLM hallucinations and provides highly accurate, context-rich answers to complex questions about the epic.

## Architecture

The system is split into two parallel retrieval pipelines that converge into a final master synthesis:

1. **Semantic Vector Search (ChromaDB)**
   - Text is chopped into small chunks and mathematically embedded into a local vector space using Google's `gemini-embedding-2`.
   - Ideal for retrieving rich story context, descriptive prose, and general thematic matching.
   - Employs a custom `RetryEmbeddings` wrapper to automatically handle API rate limits during massive indexing jobs.

2. **GraphRAG (KuzuDB)**
   - Text is processed in massive 15,000-character batches by a frontier LLM to extract complex relationships across an advanced ontology.
   - The graph tracks Nodes dynamically categorized as `Character`, `Location`, `Concept`, `Weapon`, or `Event`.
   - These facts are stored as explicit Nodes and Edges in a local Knowledge Graph.

3. **Hybrid Synthesis & Text-to-Cypher**
   - The final query engine (`hybrid_query.py`) simultaneously searches ChromaDB for context and KuzuDB for hard facts.
   - It utilizes a dedicated **Text-to-Cypher** agent that translates your question into raw mathematical database code to hunt down complex answers across the graph.
   - It synthesizes both data streams into a single Master Prompt, allowing the generation LLM to anchor its logic in the graph while drawing descriptive flavor from the vector chunks.

## Technologies Used

- **LangChain**: The core orchestration framework tying the databases, models, and fallback cascades together.
- **KuzuDB**: A hyper-fast, embeddable graph database used to store character interaction edges.
- **ChromaDB**: The local vector database used to store semantic text embeddings.
- **Google Gemini / Gemma APIs**: Powers the entire architecture 100% in the cloud via the `langchain-google-genai` integration (Vector Embeddings, Graph Extraction, Text-to-Cypher, and Final Synthesis).
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
- `query_graph.py`: A pure GraphRAG engine that extracts target entities and runs Cypher queries.
- `hybrid_query.py`: The ultimate engine that combines both Vector and Graph databases to generate the perfect answer using dynamic Text-to-Cypher logic.

## Setup & Execution

1. Install the required python dependencies:
   ```bash
   pip install langchain langchain-chroma langchain-google-genai pydantic kuzu python-dotenv
   ```
3. Create a `.env` file in the root directory and add your Google API key:
   ```env
   GOOGLE_API_KEY="your_api_key_here"
   ```
3. Run the data prep and build scripts:
   ```bash
   python scripts/download_and_prep_data.py
   python build_index.py
   python build_graph.py
   ```
4. Query the epic:
   ```bash
   python hybrid_query.py
   ```
