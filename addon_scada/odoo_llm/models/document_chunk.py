from odoo import models, fields


class LlmDocumentChunk(models.Model):
    _name = 'llm.document.chunk'
    _description = 'Document Chunk for Vector Search'

    document_id = fields.Many2one('llm.document', required=True, ondelete='cascade')
    text = fields.Text(required=True)
    embedding = fields.Text(string='Embedding')
