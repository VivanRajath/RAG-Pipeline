import os
import faiss
import numpy as np
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

embedder = SentenceTransformer("all-MiniLM-L6-v2")

# --- Directories ---
INDEX_DIR = "rag_indexes"
os.makedirs(INDEX_DIR, exist_ok=True)

GLOBAL_INDEX_PATH = os.path.join(INDEX_DIR, "global.index")
GLOBAL_DOCS_PATH = os.path.join(INDEX_DIR, "global_docs.npy")

# --- PDF Loader ---
def load_and_chunk_pdf(file_path, chunk_size=1000, chunk_overlap=200):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return text_splitter.split_text(text)

# --- Global FAISS Update ---
def update_global_faiss(docs):
    doc_embeddings = embedder.encode(docs).astype("float32")

    if os.path.exists(GLOBAL_INDEX_PATH):
        index = faiss.read_index(GLOBAL_INDEX_PATH)
        existing_docs = np.load(GLOBAL_DOCS_PATH, allow_pickle=True).tolist()
    else:
        dimension = doc_embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        existing_docs = []

    index.add(doc_embeddings)
    faiss.write_index(index, GLOBAL_INDEX_PATH)

    all_docs = existing_docs + docs
    np.save(GLOBAL_DOCS_PATH, all_docs)

# --- Process File ---
def process_file_with_rag(file_path, file_id):
    docs = load_and_chunk_pdf(file_path)
    update_global_faiss(docs)
    print(f"✅ Added {len(docs)} chunks from file {file_id} to global FAISS.")

# --- Query ---
def load_global_index_and_docs():
    index = faiss.read_index(GLOBAL_INDEX_PATH)
    docs = np.load(GLOBAL_DOCS_PATH, allow_pickle=True)
    return index, docs

def retrieve(query, index, docs, k=3):
    q_embedding = embedder.encode([query]).astype("float32")
    D, I = index.search(q_embedding, k)
    return [docs[i] for i in I[0]]

def ask_gemini(query, k=3):
    index, docs = load_global_index_and_docs()
    relevant_chunks = retrieve(query, index, docs, k)
    context = "\n\n".join(relevant_chunks)

    prompt = f"""You are an AI assistant.
    Use the following document context to answer the user's question.
    If the context does not contain the answer, say "I couldn't find that in the document."

    Context:
    {context}

    Question: {query}
    Answer:"""

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text
