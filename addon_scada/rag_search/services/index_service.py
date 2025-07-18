import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import faiss
import numpy as np

from odoo import tools
from ..services.embedder_service import EmbedderService


class RagIndexService:
    def __init__(self, env):
        self.env = env
        self.model = EmbedderService.model
        self.dim = self.model.get_sentence_embedding_dimension()
        self.index_path = os.path.join(tools.config.filestore('llm_index'), 'rag_faiss.index')
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)

    def compute_embeddings(self):
        chunks = self.env['rag.chunk'].search([('content', '!=', False)])
        for chunk in chunks:
            if not chunk.content:
                continue
            text = f"passage: {chunk.content.strip().lower()}"
            vec = self.model.encode(text, convert_to_numpy=True).astype('float32')
            if vec.shape[0] != self.dim:
                continue
            chunk.embedding = vec.tobytes()

    def build_index(self):
        chunks = self.env['rag.chunk'].search([('embedding', '!=', False)])
        vecs, ids = [], []

        for chunk in chunks:
            try:
                vec = np.frombuffer(chunk.embedding, dtype='float32')
                if vec.shape[0] == self.dim:
                    ids.append(chunk.id)
                    vecs.append(vec)
            except Exception:
                continue

        if not vecs:
            return

        vecs = np.stack(vecs).astype('float32')
        faiss.normalize_L2(vecs)

        index = faiss.IndexIDMap(faiss.IndexFlatIP(self.dim))
        index.add_with_ids(vecs, np.array(ids, dtype='int64'))
        faiss.write_index(index, self.index_path)

    def load_index(self):
        if not os.path.exists(self.index_path):
            return None
        return faiss.read_index(self.index_path)

    def search(self, query, top_k=5, threshold=0.7):
        """Поиск по FAISS индексу, возвращает список словарей результатов."""
        index = self.load_index()
        if not index:
            return []

        try:
            vec = self.model.encode(f"query: {query.strip().lower()}", convert_to_numpy=True).astype('float32')
            faiss.normalize_L2(vec.reshape(1, -1))

            scores, ids = index.search(vec.reshape(1, -1), top_k)
            result_ids = ids[0].tolist()
            result_scores = scores[0].tolist()

            records = self.env['rag.chunk'].browse(result_ids)
            id2rec = {rec.id: rec for rec in records}

            results = []
            for i, chunk_id in enumerate(result_ids):
                score = result_scores[i]
                if chunk_id == -1 or score < threshold:
                    continue
                rec = id2rec.get(chunk_id)
                if not rec:
                    continue
                results.append({
                    'id': rec.id,
                    'doc_id': rec.document_id.id,
                    'score': float(score),
                    'text': rec.content,
                    'document': rec.document_id.display_name,
                    'page_number': rec.page_number,
                    'char_start': rec.char_start,
                    'char_end': rec.char_end,
                })

            results.sort(key=lambda r: r['score'], reverse=True)
            return results

        except Exception as e:
            # _logger.exception("FAISS search failed: %s", e)
            return []
