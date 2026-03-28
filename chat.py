import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import pipeline

# ----------------------------
# 1️⃣ Ładujemy embedding model
# ----------------------------
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# ----------------------------
# 2️⃣ Ładujemy wcześniej zbudowany indeks i dokumenty
# ----------------------------
index = faiss.read_index("docs.index")
docs = np.load("docs.npy", allow_pickle=True)

# ----------------------------
# 3️⃣ Lokalny model językowy (Flan-T5 lub dowolny inny)
# Używamy text-generation, bo Transformers 5.3.0 nie ma text2text-generation
# ----------------------------
generator = pipeline(
    "text-generation",
    model="google/flan-t5-base",
    max_new_tokens=150
)

# ----------------------------
# 4️⃣ Pętla chat
# ----------------------------
print("Mini ChatGPT (na Twoich dokumentach). Wpisz 'exit', aby zakończyć.\n")

while True:
    question = input("Ty: ")
    if question.lower() in ["exit", "quit"]:
        break

    # 🔹 Zamieniamy pytanie na embedding
    q_embedding = embed_model.encode([question])

    # 🔹 Wyszukujemy najbardziej pasujący dokument w indeksie
    D, I = index.search(np.array(q_embedding), k=1)
    context = docs[I[0][0]]

    # 🔹 Tworzymy prompt dla modelu
    prompt = f"{context}\n\nPytanie: {question}\nOdpowiedź:"

    # 🔹 Generujemy odpowiedź
    result = generator(prompt)

    # 🔹 Wyciągamy wygenerowany tekst
    answer = result[0]["generated_text"].strip()

    print("AI:", answer)