from odoo import models

class LLMVectorServiceAbstract(models.AbstractModel):
    _name = 'llm.vector.service.abstract'
    _description = 'Abstract interface for vector search'

    def semantic_search(self, text: str, k: int):
        """
        Ищет k наиболее релевантных документов.
        Должно возвращать список кортежей (doc_obj, distance).
        """
        raise NotImplementedError


class LLMEmbeddingServiceAbstract(models.AbstractModel):
    _name = 'llm.embedding.service.abstract'
    _description = 'Abstract interface for text generation'

    def generate_text(self, prompt: str, history: list):
        """
        Генерирует ответ по переданным prompt и истории.
        """
        raise NotImplementedError
