import json
import numpy as np
import faiss

from sentence_transformers import SentenceTransformer
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Build FAISS index from documents"

    def handle(self, *args, **kwargs):

        model = SentenceTransformer("all-MiniLM-L6-v2")

        dump_file = "ai.json"

        # Dump database
        with open(dump_file, "w") as f:
            call_command("dumpdata", stdout=f)

        # Load JSON
        with open(dump_file, "r") as f:
            data = json.load(f)

        # Extract text fields
        docs = []
        for item in data:
            fields = item.get("fields", {})
            docs.append(str(fields))

        # Create embeddings
        embeddings = model.encode(docs)

        # Build FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)

        index.add(np.array(embeddings))

        # Save index
        faiss.write_index(index, "docs.index")
        np.save("docs.npy", np.array(docs))

        print("Index created")