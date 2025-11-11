{
    'name': "AI Claude Connector",
    'summary': "Anthropic Claude AI integration for AI Complete Suite",
    'description': """
This module extends the AI Complete Suite to support Anthropic Claude AI API integration.
    """,
    'author': "Bakum Viacheslav",
    'category': 'Productivity/AI',
    'version': '0.1',
    'depends': ['ai_base_gt'],
    'external_dependencies': {
        'python': ['anthropic>=0.5.0'],
    },
    'data': [
        'data/ai_config_data.xml',
        'views/ai_config_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
