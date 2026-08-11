import os
import warnings
warnings.filterwarnings("ignore")  # Suppress non-critical library warnings

from langchain_community.document_loaders import PyPDFDirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Configuration Paths
PDF_DIR = "data/medical_pdfs"
CHROMA_DB_DIR = "medigenie_rag_db"

def run_rag_ingestion():
    print("🚀 [Phase 10] Starting Medical Knowledge Base (RAG) Ingestion...")

    # 1. Ensure directory exists
    os.makedirs(PDF_DIR, exist_ok=True)

    # 2. Check if medical PDFs or files are available
    files = os.listdir(PDF_DIR)
    
    # If folder is empty, create a default guideline text file so DB initializes cleanly
    if not files:
        print(f"⚠️ No PDFs found in '{PDF_DIR}'. Creating sample WHO Guideline file...")
        sample_guideline = os.path.join(PDF_DIR, "sample_who_guidelines.txt")
        with open(sample_guideline, "w", encoding="utf-8") as f:
            f.write(
                "WHO Diabetes & Hypertension Guidelines 2024:\n"
                "1. Fasting Blood Sugar > 126 mg/dL indicates Diabetes Mellitus.\n"
                "2. Systolic Blood Pressure > 140 mmHg requires clinical evaluation for Hypertension.\n"
                "3. First-line treatment for Type-2 Diabetes includes Metformin along with lifestyle modification.\n"
                "4. Patients taking ACE inhibitors should avoid Potassium supplements due to Hyperkalemia risk.\n"
            )

    # 3. Load Documents (PDFs & Text files)
    print("📄 Loading documents from directory...")
    loader = PyPDFDirectoryLoader(PDF_DIR)
    documents = loader.load()

    # Fallback to TextLoader if only txt files exist
    if not documents:
        print("Loading text guidelines...")
        docs = []
        for file in os.listdir(PDF_DIR):
            if file.endswith(".txt"):
                txt_loader = TextLoader(os.path.join(PDF_DIR, file), encoding="utf-8")
                docs.extend(txt_loader.load())
        documents = docs

    print(f"✅ Loaded {len(documents)} document page(s).")

    # 4. Chunk Documents into smaller text blocks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = text_splitter.split_documents(documents)
    print(f"🧩 Split into {len(chunks)} text chunks.")

    # 5. Generate HuggingFace Embeddings & Save to ChromaDB
    print("🧠 Generating embeddings with 'all-MiniLM-L6-v2'...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR
    )

    print(f"💾 Knowledge Base saved successfully at '{CHROMA_DB_DIR}'!")

if __name__ == "__main__":
    run_rag_ingestion()