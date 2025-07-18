# import os

from odoo import models, fields, api, tools
# import faiss
# import numpy as np

from ..services.embedder_service import EmbedderService

# FAISS_INDEX_PATH = tools.config.filestore('llm_index')  # папка внутри Odoo-файлов
#
# # Убедимся, что директория существует
# os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
# INDEX_FILE = os.path.join(FAISS_INDEX_PATH, 'rag_faiss.index')

class RagChunk(models.Model):
    _name = "rag.chunk"
    _description = "RAG Chunk"

    document_id = fields.Many2one("rag.document", ondelete="cascade")
    content = fields.Text("Text Chunk")
    position = fields.Integer("Position")
    page_number = fields.Integer("Page Number")
    char_start = fields.Integer("Start Char Index")
    char_end = fields.Integer("End Char Index")
    embedding = fields.Binary("Embedding")

    # @api.depends('content')
    # def _compute_embedding(self):
    #     model = EmbedderService.model
    #     dim = model.get_sentence_embedding_dimension()  # например, 384
    #     for chunk in self:
    #         if not chunk.content:
    #             chunk.embedding = False
    #             continue
    #         text = f"passage: {chunk.content.strip().lower()}"
    #         vec = model.encode(text, convert_to_numpy=True).astype('float32')
    #         vec = vec.astype('float32')
    #         # проверка размера
    #         if vec.shape[0] != dim:
    #             raise ValueError(f"Embedding dim mismatch: got {vec.shape[0]}, expected {dim}")
    #         chunk.embedding = vec.tobytes()

    # @api.model
    # def _build_index(self):
    #     model = EmbedderService.model
    #     dim = model.get_sentence_embedding_dimension()
    #
    #     valid = []
    #     vecs = []
    #
    #     for ch in self.search([('embedding', '!=', False)]):
    #         try:
    #             vec = np.frombuffer(ch.embedding, dtype='float32')
    #             if vec.shape[0] == dim:
    #                 valid.append(ch.id)
    #                 vecs.append(vec)
    #         except Exception:
    #             continue  # Пропустить битые эмбеддинги
    #
    #     if not vecs:
    #         return
    #
    #     vecs = np.stack(vecs).astype('float32')
    #     faiss.normalize_L2(vecs)
    #
    #     index = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
    #     index.add_with_ids(vecs, np.array(valid, dtype='int64'))
    #
    #     faiss.write_index(index, INDEX_FILE)
