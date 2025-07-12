import faiss
import numpy as np
from odoo import api, models

class VectorIndex(models.TransientModel):
    _name = "llm.vector.index"
    _description = "FAISS Vector Index"

    index = None

    @api.model
    def build_index(self):
        docs = self.env['llm.document'].search([])
        vectors, ids = [], []
        for doc in docs:
            vec = self.env['llm.embedding_service'].deserialize(doc.embedding)
            vectors.append(vec)
            ids.append(doc.id)
        if not vectors:
            return []
        dim = len(vectors[0])
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(np.array(vectors, dtype='float32'))
        return ids

    def search(self, q_vec, top_k=5):
        xq = np.array([q_vec], dtype='float32')
        dists, idxs = self.index.search(xq, top_k)
        return idxs[0], dists[0]