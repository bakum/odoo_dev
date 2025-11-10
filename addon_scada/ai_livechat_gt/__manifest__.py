{
    'name': "AI Livechat GT",
    'version': '17.0.1.0',
    'category': 'Productivity/AI',
    'summary': "Integrates AI Assistants with Odoo Mail (Discuss) menu",
    'author': "Bakum Viacheslav",
    'depends': [
        'mail',
        'ai_base_gt', 
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ai_assistant_security.xml',
        'views/ai_assistant_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'ai_livechat_gt/static/src/discuss_component.js',
        ],
    },
}