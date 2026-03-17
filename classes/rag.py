import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import json
import faiss

class FaissStore:
    def __init__(self, index_path, model_name="all-MiniLM-L6-v2"):
        self.index_path = Path(index_path)
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
        else:
            base_index = faiss.IndexFlatL2(self.dim)
            self.index = faiss.IndexIDMap(base_index)

    def load_metadata(self, path=""):
        with open("vector_db/meta.json") as f:
            data = json.load(f)
            self.meta = data

    def embed(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        return self.model.encode(texts, convert_to_numpy=True).astype("float32")

    def add(self, texts, ids):
        vectors = self.embed(texts)
        ids = np.array(ids, dtype="int64")
        self.index.add_with_ids(vectors, ids)
        self.save()

    def search(self, query, k=5):
        q = self.embed(query)
        distances, ids = self.index.search(q, k)
        return distances[0], ids[0]

    def save(self):
        faiss.write_index(self.index, str(self.index_path))

class MetadataStore:
    def __init__(self, meta_path):
        self.meta_path = Path(meta_path)
        if self.meta_path.exists():
            with open(self.meta_path) as f:
                self.meta = json.load(f)
        else:
            raise FileNotFoundError(f"Metadata file {meta_path} not found.")
            self.meta = {}

        self.texts = []
        self.ids = []
        for doc_id, _meta in self.meta.items():
            self.texts.append(_meta["text"])
            self.ids.append(int(doc_id))

    def add_metadata(self, id, metadata):
        self.meta[str(id)] = metadata
        self.save()

    def get_metadata(self, id):
        return self.meta.get(str(id), None)

    def save(self):
        with open(self.meta_path, "w") as f:
            json.dump(self.meta, f)

meta_store = MetadataStore("LLM_Practice/vector_db/meta.json")
store = FaissStore("vector_index.faiss")
store.add(meta_store.texts, meta_store.ids)

dists, idxs = store.search("distance between turbine 2 and 4", k=5)
print(idxs)  # should be your custom IDs, e.g. [2, ...]

print(meta_store.get_metadata(idxs[0])["text"])

class RAG:
    def __init__(self, meta_path, faiss_path):
        self.meta_store = MetadataStore(meta_path)
        self.vector_store = FaissStore(faiss_path)
        store.add(meta_store.texts, meta_store.ids) # Add all metadata to vector store

    def retrieve(self, query, k=5):
        dists, idxs = self.vector_store.search(query, k)
        results = []
        for idx in idxs:
            meta = self.meta_store.get_metadata(idx)
            if meta:
                results.append(meta["text"])
        return results
  
meta_path = "C:/Users/lj200/OneDrive/Documents/GitHub/Streamlit-NSGA-III/LLM_Practice/vector_db/meta.json"
faiss_path = "C:/Users/lj200/OneDrive/Documents/GitHub/Streamlit-NSGA-III/LLM_Practice/vector_db/vector_index.faiss"
rag = RAG(meta_path, faiss_path)
print(rag.retrieve("distance between turbine 2 and 4"))
print(rag.retrieve("Power generation at a wind speed of 10 m/s"))

