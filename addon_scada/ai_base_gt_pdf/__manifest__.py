{
    'name': "AI Base GT - PDF Connector (fitz, Multi-PDF)",
    'version': '18.0.0.1',
    'category': 'Productivity/AI',
    'summary': "Adds Multi-PDF file support (using fitz) to AI Data Sources",
    'author': "Bakum Viacheslav",
    'depends': [
        'ai_base_gt',
    ],
    'data': [
        'security/ir.model.access.csv', # <-- Добавили новый файл
        'views/ai_data_source_views.xml',
        'views/ai_data_item_views.xml', # <-- ДОБАВЛЕН
    ],
    'external_dependencies': {
        'python': [
            'PyMuPDF',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}