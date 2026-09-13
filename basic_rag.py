import os
import warnings
warnings.filterwarnings("ignore")

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_ollama.llms import OllamaLLM
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

def main():
    print("1. Initializing models from local Ollama...")
    llm = OllamaLLM(model="llama3.2")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    print("2. Loading documents from 'data/' directory...")
    loader = DirectoryLoader('./data', glob="**/*.txt", loader_cls=TextLoader)
    docs = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
    splits = text_splitter.split_documents(docs)
    
    print("3. Setting up local ChromaDB vector store...")
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory="./chroma_db")
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    
    print("4. Creating Query Engine...")
    system_prompt = (
        "You are a highly intelligent assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer the question. "
        "Calculate sums if necessary based on the documents. "
        "\n\n"
        "Context:\n{context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    print("\n--- Indexing Complete. Type 'exit' to quit. ---\n")
    
    while True:
        question = input("\nAsk a question: ")
        if question.lower() in ['exit', 'quit']:
            break
            
        print("Thinking (Sending retrieved chunks to Llama 3.2)...\n")
        response = rag_chain.invoke({"input": question})
        
        print("\n=== FINAL ANSWER ===")
        print(response["answer"])
        print("====================")
        
        print("\nSource Chunks retrieved from Vector Database to answer this:")
        for i, doc in enumerate(response["context"]):
            print(f"\n[Source {i+1}]")
            print(f"Snippet: {doc.page_content.strip()}")

if __name__ == "__main__":
    main()
