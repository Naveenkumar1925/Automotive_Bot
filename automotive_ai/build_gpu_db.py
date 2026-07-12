import os
import glob
import easyocr
import fitz
import torch
from dotenv import load_dotenv
from tqdm import tqdm

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_weaviate.vectorstores import WeaviateVectorStore

import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Property, DataType, Configure
import weaviate.classes.init as wvc_init

# ========= CONFIG =========

load_dotenv()

DOCUMENT_FOLDER = r"data\output_pdf"
COLLECTION_NAME = "EdgeGPUCollection"

OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_API_BASE_URL = "http://localhost:11434"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print("🔥 GPU:", DEVICE)

# ========= GPU OCR =========

reader = easyocr.Reader(['en'], gpu=(DEVICE=="cuda"))

def process_pdf(pdf_path):

    docs = []

    pdf = fitz.open(pdf_path)

    for i in range(len(pdf)):

        page = pdf[i]
        pix = page.get_pixmap(dpi=200)
        img = torch.frombuffer(pix.samples, dtype=torch.uint8)
        img = img.reshape(pix.height, pix.width, pix.n).numpy()

        result = reader.readtext(img, detail=0)
        text = "\n".join(result)

        if text.strip():

            docs.append(
                Document(
                    page_content=text,
                    metadata={"source": pdf_path}
                )
            )

    return docs


# ========= LOAD DOCUMENTS =========

all_docs = []

pdfs = glob.glob(os.path.join(DOCUMENT_FOLDER,"**/*.pdf"),recursive=True)

for pdf in tqdm(pdfs,desc="GPU OCR"):
    all_docs.extend(process_pdf(pdf))

# ========= SPLIT =========

splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=100
)

chunks = splitter.split_documents(all_docs)

print("Chunks:",len(chunks))

# ========= WEAVIATE =========

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=os.environ["WEAVIATE_URL"],
    auth_credentials=Auth.api_key(os.environ["WEAVIATE_API_KEY"]),
    skip_init_checks=True,
    additional_config=wvc_init.AdditionalConfig(
        timeout=wvc_init.Timeout(init=60)
    )
)

if client.collections.exists(COLLECTION_NAME):
    client.collections.delete(COLLECTION_NAME)

client.collections.create(
    name=COLLECTION_NAME,
    properties=[
        Property(name="text", data_type=DataType.TEXT)
    ],
    vectorizer_config=Configure.Vectorizer.text2vec_ollama(
        model=OLLAMA_EMBEDDING_MODEL,
        api_endpoint=OLLAMA_API_BASE_URL
    )
)

embeddings = OllamaEmbeddings(
    model=OLLAMA_EMBEDDING_MODEL,
    base_url=OLLAMA_API_BASE_URL
)

WeaviateVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings,
    client=client,
    index_name=COLLECTION_NAME
)

print("🔥 DB BUILD COMPLETE")
"""

import os
import glob
import fitz
import easyocr
import torch
import numpy as np
from tqdm import tqdm

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings

# ================= CONFIG =================

PDF_FOLDER = "data/output_pdf"
VECTOR_DB_DIR = "vector_db"

OCR_BATCH_SIZE = 5   # increase to 12 or 16 if GPU memory allows

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print("\n========== SYSTEM ==========")
print("GPU:", DEVICE)
print("OCR Batch Size:", OCR_BATCH_SIZE)
print("============================\n")

# ================= LOAD OCR =================

print("Loading EasyOCR...")
reader = easyocr.Reader(['en'], gpu=(DEVICE=="cuda"))
print("OCR ready\n")

# ================= FIND PDF FILES =================

pdf_files = glob.glob(os.path.join(PDF_FOLDER,"*.pdf"))

print("PDF files:", len(pdf_files))
print()

# ================= TEXT SPLITTER =================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=100
)

chunks = []

# ================= MAIN PIPELINE =================

for pdf_path in tqdm(pdf_files, desc="PDF files", unit="pdf"):

    try:
        pdf = fitz.open(pdf_path)
    except:
        print("Failed:", pdf_path)
        continue

    pages = list(pdf)

    for i in tqdm(range(0, len(pages), OCR_BATCH_SIZE),
                  desc=os.path.basename(pdf_path),
                  leave=False):

        batch = pages[i:i+OCR_BATCH_SIZE]

        images = []

        for page in batch:

            pix = page.get_pixmap(dpi=200)

            img = np.frombuffer(pix.samples, dtype=np.uint8).copy()
            img = img.reshape(pix.height, pix.width, pix.n)

            images.append(img)

        # ===== GPU OCR BATCH =====
        results = reader.readtext_batched(images, detail=0)

        for text_result in results:

            text = "\n".join(text_result)

            if text.strip():

                doc = Document(
                    page_content=text,
                    metadata={"source": os.path.basename(pdf_path)}
                )

                split = splitter.split_documents([doc])

                chunks.extend(split)

print("\nTotal chunks:", len(chunks))

# ================= EMBEDDINGS =================

print("\nLoading embedding model...")

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

print("Generating FAISS index...")

vector_db = FAISS.from_documents(
    tqdm(chunks, desc="Embedding chunks"),
    embeddings
)

# ================= SAVE DB =================

os.makedirs(VECTOR_DB_DIR, exist_ok=True)

vector_db.save_local(VECTOR_DB_DIR)

print("\n========== BUILD COMPLETE ==========")
print("Vector DB saved in:", VECTOR_DB_DIR)
print("Total chunks:", len(chunks))
print("====================================")
"""