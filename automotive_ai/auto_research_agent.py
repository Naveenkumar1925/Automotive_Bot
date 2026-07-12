import time
import requests
import chromadb
import ollama
from bs4 import BeautifulSoup

CHROMA_DB = "./car_chroma_db"

client = chromadb.PersistentClient(path=CHROMA_DB)
collection = client.get_or_create_collection("cars")

EMBED_MODEL = "nomic-embed-text"

# =============================
# SCRAPE NEW CAR DATA
# =============================

def crawl_new_cars():

    print("Scanning web for new cars...")

    url = "https://www.caranddriver.com"

    r = requests.get(url, timeout=10)

    soup = BeautifulSoup(r.text, "html.parser")

    texts = []

    for a in soup.select("a")[:50]:
        text = a.get_text().strip()

        if len(text) > 20 and "car" in text.lower():
            texts.append(text)

    return texts

# =============================
# UPDATE VECTOR DB
# =============================

def update_db():

    new_data = crawl_new_cars()

    if not new_data:
        print("No new data found.")
        return

    current_count = collection.count()

    for i, text in enumerate(new_data):

        try:
            embedding = ollama.embeddings(
                model=EMBED_MODEL,
                prompt=text   # ✅ single string now
            )["embedding"]

            collection.add(
                ids=[str(current_count + i)],
                documents=[text],
                embeddings=[embedding]
            )

        except Exception as e:
            print("Skipped one entry:", e)

    print("Database updated successfully.")

# =============================
# AUTONOMOUS LOOP
# =============================

if __name__ == "__main__":

    while True:

        update_db()

        print("Sleeping for 24 hours...")

        time.sleep(60 * 60 * 24)