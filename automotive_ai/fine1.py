import os
import fitz
import re
import time
from tqdm import tqdm
from langchain_ollama import ChatOllama

# ========== CONFIG ==========
INPUT_FOLDER = "/home/superuser/Desktop/automotive_ai/data/output_pdf"
OUTPUT_FOLDER = "/home/superuser/Desktop/automotive_ai/data/output_pdf/output_txt"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

MODEL_NAME = "llama3:8b"

# Stable for 12GB VRAM
MAX_WORKERS = 1   # DO NOT increase for quality

CHUNK_SIZE = 2500

# ========== LLM ==========
llm = ChatOllama(
    model=MODEL_NAME,
    temperature=0
)

# ========== EXTRACT ==========
def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    return "".join([page.get_text() for page in doc])

# ========== CLEAN ==========
def clean_text(text):
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ========== CHUNK ==========
def chunk_text(text, size=CHUNK_SIZE):
    return [text[i:i+size] for i in range(0, len(text), size)]

# ========== PASS 1 ==========
def structure_chunk(chunk):
    prompt = f"""
You are an expert document editor.

Transform this into a structured document:

- Remove noise
- Add headings
- Keep meaning exact
- Organize into sections
- Use bullet points where useful

TEXT:
{chunk}
"""
    return llm.invoke(prompt).content

# ========== PASS 2 ==========
def refine_chunk(chunk):
    prompt = f"""
Refine this structured document:

- Improve clarity
- Fix formatting consistency
- Ensure logical flow
- Remove duplication

TEXT:
{chunk}
"""
    return llm.invoke(prompt).content

# ========== PROCESS ==========
def process_pdf(file_name, file_index, total_files):
    import time
    start_time = time.time()

    input_path = os.path.join(INPUT_FOLDER, file_name)

    print(f"\n📄 [{file_index}/{total_files}] Processing: {file_name}")

    # -------- EXTRACT --------
    print("🔹 Stage 1: Extracting text...")
    raw = extract_text(input_path)

    # -------- CLEAN --------
    print("🔹 Stage 2: Cleaning text...")
    cleaned = clean_text(raw)

    # -------- CHUNK --------
    chunks = chunk_text(cleaned)
    total_chunks = len(chunks)

    print(f"🔹 Total chunks: {total_chunks}")

    # TOTAL STEPS (pass1 + pass2)
    total_steps = total_chunks * 2
    completed_steps = 0

    # 🔥 FILE LEVEL PROGRESS BAR
    file_pbar = tqdm(total=total_steps, desc="📊 File Progress", position=0)

    # -------- PASS 1 --------
    structured_chunks = []
    print("🔹 Stage 3: Structuring (Pass 1)...")

    for chunk in tqdm(chunks, desc="Pass 1", position=1, leave=False):
        result = structure_chunk(chunk)
        structured_chunks.append(result)

        completed_steps += 1
        file_pbar.update(1)

    # -------- PASS 2 --------
    refined_chunks = []
    print("🔹 Stage 4: Refining (Pass 2)...")

    for chunk in tqdm(structured_chunks, desc="Pass 2", position=1, leave=False):
        result = refine_chunk(chunk)
        refined_chunks.append(result)

        completed_steps += 1
        file_pbar.update(1)

    file_pbar.close()

    # -------- MERGE --------
    final_text = "\n\n".join(refined_chunks)

    # -------- SAVE --------
    print("🔹 Stage 5: Saving TXT...")
    output_path = os.path.join(
        OUTPUT_FOLDER,
        file_name.replace(".pdf", ".txt")
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_text)

    end_time = time.time()

    print(f"✅ Completed: {file_name}")
    print(f"⏱ Time taken: {round(end_time - start_time, 2)} sec")

# ========== MAIN ==========
if __name__ == "__main__":
    files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".pdf")]

    total_files = len(files)

    print(f"🚀 Starting processing of {total_files} PDFs\n")

    for idx, file in enumerate(files, start=1):
        process_pdf(file, idx, total_files)

    print("\n🎉 ALL FILES PROCESSED SUCCESSFULLY")