from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
from pathlib import Path
from app.catalog import catalog

class Retriever:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.items = None
        self._build_index()

    def _build_index(self):
        self.items = catalog.get_all()
        if not self.items:
            print("⚠️ No items in catalog")
            return

        texts = []
        for item in self.items:
            text = f"{item.get('name', '')} {item.get('description', '')} {' '.join(item.get('keys', []))} {' '.join(item.get('job_levels', []))}"
            texts.append(text)

        embeddings = self.model.encode(texts, normalize_embeddings=True)
        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings.astype(np.float32))

        # Save index
        Path("data").mkdir(exist_ok=True)
        with open("data/faiss_index.pkl", "wb") as f:
            pickle.dump((self.index, self.items), f)

        print(f"✅ FAISS index built with {len(self.items)} assessments")

    def search(self, query: str, top_k: int = 15):
        if not self.index:
            return []
        
        qvec = self.model.encode([query], normalize_embeddings=True)
        distances, indices = self.index.search(qvec.astype(np.float32), top_k)
        
        results = []
        for i in indices[0]:
            if i < len(self.items):
                item = self.items[i].copy()
                item['url'] = item.get('link')  # Map link → url
                results.append(item)
        return results

retriever = Retriever()