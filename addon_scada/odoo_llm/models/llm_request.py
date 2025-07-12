from odoo import api, fields, models

class LLMRequest(models.Model):
    _name = "llm.request"
    _description = "LLM-requests history"

    name     = fields.Char("Description", required=True)
    prompt   = fields.Text("Request")
    response = fields.Text("Response")
    date     = fields.Datetime("Time", default=fields.Datetime.now)

    def action_generate(self):
        for rec in self:
            rec.response = self.env['llm.embedding_service'].generate_text(rec.prompt)