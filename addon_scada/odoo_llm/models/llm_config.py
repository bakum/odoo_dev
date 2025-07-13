from odoo import fields, models


class LlmConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    llm_model_name = fields.Selection(
        selection=[
            ('llama3', 'LLaMA 3'),
            ('llama3:70b', 'LLaMA 3 (Meta)'),
            ('mistral', 'Mistral'),
            ('mixtral', 'Mistral / Mixtral (Mistral.ai)'),
            ('gemma', 'Gemma'),
            ('codellama', 'CodeLLaMA'),
        ],
        string='LLM Model Name',
        default='llama3',
        config_parameter='odoo_llm.llm_model_name',
    )

    ollama_entrypoint = fields.Char(string='Ollama Entrypoint', default='http://localhost:11434',
                                        config_parameter='odoo_llm.ollama_entrypoint', )