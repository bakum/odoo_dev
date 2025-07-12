from odoo import api, models

class VectorService(models.AbstractModel):
    _name = "llm.vector.service"
    _description = "Vector Search Service"

    @api.model
    def index_all(self):
        return self.env['llm.vector.index'].build_index()

    @api.model
    def semantic_search(self, query, k=5):
        emb = self.env['llm.embedding_service'].embed(query)
        idxs, dists = self.env['llm.vector.index'].search(emb, top_k=k)
        docs = self.env['llm.document'].browse(idxs)
        return list(zip(docs, dists))