import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import pipeline

class AIEngine:

    def __init__(self):
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")

        self.index = faiss.read_index("docs.index")
        self.docs = np.load("docs.npy", allow_pickle=True)

        self.generator = pipeline(
            "text-generation",  # możesz zmienić później
            model="google/flan-t5-base",
            max_new_tokens=150
        )

    def ask(self, question):
        q_embedding = self.embed_model.encode([question])

        D, I = self.index.search(np.array(q_embedding), k=3)
        context = " ".join([self.docs[i] for i in I[0]])

        prompt = f"""
        Odpowiedz na pytanie na podstawie kontekstu.

        Kontekst:
        {context}

        Pytanie:
        {question}

        Odpowiedź:
        """

        result = self.generator(prompt)
        return result[0]["generated_text"].strip()


# 🔥 globalna instancja (ładowana raz)
ai_engine = AIEngine()