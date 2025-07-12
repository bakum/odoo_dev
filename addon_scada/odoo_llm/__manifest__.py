{
    "name": "LLM Integration with RAG",
    'version': '17.0.0.1',
    'author': 'Bakum Viacheslav',
    'website': 'https://optimus.com.ua',
    "summary": "LLM RAG Integration Document Parsing Vectors Chatbot",
    "description": """
    Модуль odoo_llm, который обеспечивает:
            - HTTP-запросы к LLM (OpenAI)
            - Историю запросов
            - Извлечение текста из PDF/DOCX
            - Генерацию и хранение эмбеддингов
            - FAISS-индекс для семантического поиска
            - Retrieval-Augmented Generation (RAG) в чат-боте
            - Веб-виджет для интерактивного диалога в интерфейсе Odoo 17
    """,
    "category": "Tools",
    "data": [
        "security/ir.model.access.csv",
        "data/cron.xml",
        "views/llm_templates.xml",
        "views/document_views.xml",
        "views/chat_views.xml",
        "views/templates.xml",
    ],
    "installable": True,
    "application": False,
    "external_dependencies": {
        "python":
          ["requests",
           "PyPDF2",
           "python-docx",
           "faiss-cpu",
           "numpy",
           "sentence_transformers",
           "langdetect"
           ]
    },
    'assets': {
            'web.assets_backend': [
            'odoo_llm/static/src/js/chat_widget.js',
            'odoo_llm/static/src/js/chat_widget.xml',
        ],
    },
    "depends": ["web", "base"],
}
