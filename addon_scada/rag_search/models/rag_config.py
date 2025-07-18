from odoo import fields, models


class RagConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    rag_llm_model_name = fields.Selection(
        selection=[
            ('llama3', 'LLaMA 3'),
            ('nous-hermes2', 'Nous Hermes 2 - LLaMA 2 13B'),
            ('nous-hermes2:mistral', 'Nous Hermes 2 - Mistral 7B'),
            ('llama3:70b', 'LLaMA 3 (Meta)'),
            ('mistral', 'Mistral'),
            ('mixtral', 'Mistral / Mixtral (Mistral.ai)'),
            ('gemma', 'Gemma'),
            ('codellama', 'CodeLLaMA'),
        ],
        string='LLM Model Name',
        default='llama3',
        config_parameter='rag_search.rag_llm_model_name',
    )

    rag_ollama_entrypoint = fields.Char(string='Ollama Entrypoint', default='http://localhost:11434',
                                        config_parameter='rag_search.rag_ollama_entrypoint', )