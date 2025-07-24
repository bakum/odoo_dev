from odoo import models, fields, api


class RagEntity(models.Model):
    _name = 'rag.entity'
    _description = 'Entity in Knowledge Graph'

    name = fields.Char(required=True)
    entity_type = fields.Char()

    @api.model
    def _get_or_create(self, name):
        entity = self.search([('name', '=', name)], limit=1)
        return entity or self.create({'name': name})
