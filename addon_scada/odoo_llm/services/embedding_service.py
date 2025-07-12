# import openai
# import json
# from odoo import api, models
#
# class EmbeddingService(models.AbstractModel):
#     _name = "llm.embedding_service"
#     _description = "Embedding Service"
#
#     @api.model
#     def embed(self, text):
#         resp = openai.Embedding.create(
#             model="text-embedding-ada-002",
#             input=text
#         )
#         return resp["data"][0]["embedding"]
#
#     def serialize(self, vector):
#         return json.dumps(vector)
#
#     def deserialize(self, blob):
#         return json.loads(blob)

import requests
import json
from odoo import api, models
from sentence_transformers import SentenceTransformer

class TextPlusEmbeddingService(models.AbstractModel):
    _name = "llm.embedding_service"
    _description = "Text Generation + Embedding Service"

    _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Загружается один раз при инициализации

    @api.model
    def _get_llm_model(self):
        return self.env['ir.config_parameter'].sudo().get_param('odoo_llm.llm_model_name', default='llama3')

    @api.model
    def _get_entrypoint(self):
        return self.env['ir.config_parameter'].sudo().get_param('odoo_llm.ollama_entrypoint', default='http://localhost:11434/api/chat')

    @api.model
    def generate_text(self, prompt):
        res = requests.post(
            self._get_entrypoint(),
            json={
                "model": self._get_llm_model(),
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            }
        )
        res.raise_for_status()
        return res.json()["message"]["content"]

    @api.model
    def embed(self, text):
        vector = self._embedding_model.encode(text).tolist()
        return vector

    def serialize(self, vector):
        return json.dumps(vector)

    def deserialize(self, blob):
        return json.loads(blob)