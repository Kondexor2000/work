import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

# ----------------------------
# 1️⃣ Embedding model
# ----------------------------
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# ----------------------------
# 2️⃣ Indeks + dokumenty
# ----------------------------
index = faiss.read_index("docs.index")
docs = np.load("docs.npy", allow_pickle=True)

# ----------------------------
# 3️⃣ Model QA (Flan-T5)
# ----------------------------
qa_generator = pipeline(
    "text-generation",  
    model="google/flan-t5-base",
    max_new_tokens=150
)

# ----------------------------
# 4️⃣ Model do pomysłów (GPT2 PL)
# ----------------------------
IDEA_MODEL = "radlab/polish-gpt2-small-v2"

idea_tokenizer = AutoTokenizer.from_pretrained(IDEA_MODEL)
idea_model = AutoModelForCausalLM.from_pretrained(IDEA_MODEL)

if idea_tokenizer.pad_token_id is None:
    idea_tokenizer.pad_token = idea_tokenizer.eos_token

idea_generator = pipeline(
    "text-generation",
    model=idea_model,
    tokenizer=idea_tokenizer,
    device=0 if torch.cuda.is_available() else -1
)

# ----------------------------
# 5️⃣ banned words (raz!)
# ----------------------------
try:
    with open("docs/pliknot.txt", "r", encoding="utf-8") as f:
        banned_words = [line.strip().lower() for line in f.readlines()]
except:
    banned_words = []

# ----------------------------
# 6️⃣ Chat loop
# ----------------------------
print("Mini ChatGPT (na Twoich dokumentach). Wpisz 'exit', aby zakończyć.\n")

while True:
    question = input("Ty: ")

    if question.lower() in ["exit", "quit"]:
        break

    # 🔒 filtr
    if any(word in question.lower() for word in banned_words):
        print("AI: Nie mogę wygenerować tekstów naruszających zasady etyczne.")
        continue

    # 🔎 embedding
    q_embedding = embed_model.encode([question])
    faiss.normalize_L2(q_embedding)

    # 🔎 search
    D, I = index.search(np.array(q_embedding), k=5)
    context = docs[I[0][0]]

    # 🧠 prompt QA
    prompt = f"""
Odpowiedz na pytanie na podstawie kontekstu.

Kontekst:
{context}

Pytanie:
{question}

Odpowiedź:
"""

    result = qa_generator(prompt)
    answer = result[0]["generated_text"].strip()

    # 💡 generowanie pomysłów (opcjonalne)
    idea_prompt = f"Temat: {answer}\nPomysły:\n"

    ideas_output = idea_generator(
        idea_prompt,
        max_new_tokens=60,
        do_sample=True,
        temperature=0.9,
        top_p=0.9,
        num_return_sequences=3
    )

    ideas = []
    for o in ideas_output:
        text = o["generated_text"].replace(idea_prompt, "").strip()
        ideas.append(text.split("\n")[0])

    # 📢 output
    print("\nAI:", answer)

    if ideas:
        print("\n💡 Pomysły:")
        for i, idea in enumerate(ideas, 1):
            print(f"{i}. {idea}")

    print("\n" + "-"*50)