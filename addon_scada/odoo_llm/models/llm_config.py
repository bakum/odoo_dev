from odoo import fields, models


class LlmConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    llm_model_name = fields.Char(string='LLM Model Name',
                                        default='llama3',
                                        config_parameter='odoo_llm.llm_model_name', )

    ollama_entrypoint = fields.Char(string='Ollama Entrypoint', default='http://localhost:11434/api/chat',
                                        config_parameter='odoo_llm.ollama_entrypoint', )