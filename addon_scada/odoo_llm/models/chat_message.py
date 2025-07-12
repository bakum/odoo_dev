from odoo import fields, models

class ChatMessage(models.Model):
    _name = "llm.chat.message"
    _description = "Chat Message"

    session_id = fields.Many2one("llm.chat.session", ondelete="cascade")
    author     = fields.Selection(
        [("user","User"),("bot","Bot")],
        default="user"
    )
    content = fields.Text("Text")
    date    = fields.Datetime("Date", default=fields.Datetime.now)