from odoo import fields, models

class ChatSession(models.Model):
    _name = "llm.chat.session"
    _description = "LLM Chat Session"

    name        = fields.Char("Session", default="New")
    message_ids = fields.One2many("llm.chat.message", "session_id", string="Messages")

    def open_chat(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web#action=odoo_llm.llm_chat_web&model=llm.chat.session&res_id={self.id}',
            'name': 'Chat Session',
            'target': 'self',
        }