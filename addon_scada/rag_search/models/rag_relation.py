from odoo import models, fields


class RagRelation(models.Model):
    _name = 'rag.relation'
    _description = 'Relation between entities in Knowledge Graph'

    subject_id = fields.Many2one('rag.entity', required=True, ondelete="cascade")
    object_id = fields.Many2one('rag.entity', required=True, ondelete="cascade")
    relation = fields.Char(required=True)
    document_id = fields.Many2one('rag.document', ondelete="cascade")
