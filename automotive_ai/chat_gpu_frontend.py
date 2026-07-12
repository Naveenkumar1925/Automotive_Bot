import os
import re
from dotenv import load_dotenv

import weaviate
from weaviate.classes.init import Auth

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_weaviate.vectorstores import WeaviateVectorStore

from automotive_ai.car_predictor import predict_car

# ================= CONFIG =================

load_dotenv()

COLLECTION_NAME = "EdgeGPUCollection"
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_LLM_MODEL = "gemma3:latest"
OLLAMA_API_BASE_URL = "http://localhost:11434"

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
PATH_REGEX = r'(?:[a-zA-Z]:\\|[a-zA-Z]:/|[.\\/]+)[^\s"\']+(?:\.jpg|\.jpeg|\.png|\.bmp|\.webp)'


class AutomotiveChatbot:

    def __init__(self):
        print("Connecting to Weaviate Cloud...")

        self.client = weaviate.connect_to_weaviate_cloud(
            cluster_url=os.environ["WEAVIATE_URL"],
            auth_credentials=Auth.api_key(os.environ["WEAVIATE_API_KEY"]),
            skip_init_checks=True
        )

        if not self.client.collections.exists(COLLECTION_NAME):
            self.client.close()
            raise RuntimeError(
                f"Collection '{COLLECTION_NAME}' does not exist."
            )

        self.embeddings = OllamaEmbeddings(
            model=OLLAMA_EMBEDDING_MODEL,
            base_url=OLLAMA_API_BASE_URL
        )

        self.vector_store = WeaviateVectorStore(
            client=self.client,
            embedding=self.embeddings,
            index_name=COLLECTION_NAME,
            text_key="page_content"
        )

        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 8}
        )

        self.llm = ChatOllama(
            model=OLLAMA_LLM_MODEL,
            base_url=OLLAMA_API_BASE_URL,
            temperature=0.1
        )

        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are an automotive AI assistant.

Answer ONLY from the supplied context.

If the answer is not contained in the context, reply exactly:
"I couldn't find that information in the knowledge base."

Do not make up specifications.
Mention source information only if available.

Context:
{context}
"""
            ),
            ("human", "{input}")
        ])

        self.parser = StrOutputParser()

    def format_docs(self, docs):
        parts = []

        for d in docs:
            src = d.metadata.get("source", "Unknown")
            page = d.metadata.get("page", "?")

            parts.append(
                f"[Source: {src}, Page: {page}]\n{d.page_content}"
            )

        return "\n\n".join(parts)

    def chat(self, user_input):

        image_path = None

        if os.path.isfile(user_input) and user_input.lower().endswith(IMAGE_EXTENSIONS):
            image_path = user_input
        else:
            m = re.search(PATH_REGEX, user_input)
            if m:
                candidate = m.group(0).strip("\"'")
                if os.path.isfile(candidate):
                    image_path = candidate

        # ---------------- Image Prediction ----------------

        if image_path:

            result = predict_car(image_path)

            if "error" in result:
                return {
                    "answer": result["error"],
                    "sources": []
                }

            return {
                "answer":
                    f"{result['color']} "
                    f"{result['year']} "
                    f"{result['brand']} "
                    f"{result['model']}",
                "sources": []
            }

        # ---------------- RAG Search ----------------

        docs = self.retriever.invoke(user_input)

        if not docs:
            return {
                "answer": "I couldn't find anything relevant.",
                "sources": []
            }

        context = self.format_docs(docs)

        answer = (
            self.prompt
            | self.llm
            | self.parser
        ).invoke(
            {
                "context": context,
                "input": user_input
            }
        )

        sources = []

        shown = set()

        for d in docs:

            src = d.metadata.get("source", "Unknown")
            page = d.metadata.get("page", "?")

            key = (src, page)

            if key not in shown:
                shown.add(key)
                sources.append(
                    {
                        "source": src,
                        "page": page
                    }
                )

        return {
            "answer": answer,
            "sources": sources
        }

    def close(self):
        self.client.close()


# ---------------- Standalone Mode ----------------

if __name__ == "__main__":

    bot = AutomotiveChatbot()

    print("\n========== Automotive RAG Chatbot ==========")
    print("Type 'exit' to quit.\n")

    try:

        while True:

            try:
                q = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break

            if not q:
                continue

            if q.lower() == "exit":
                break

            result = bot.chat(q)

            print("\nBot:\n")
            print(result["answer"])

            if result["sources"]:
                print("\nSources:")
                for s in result["sources"]:
                    print(f" - {s['source']} (Page {s['page']})")

            print()

    finally:
        bot.close()