{
    'name': 'NW Server',
    'author': 'Bakum Viacheslav',
    'website': 'https://optimus.com.ua',
    'summary': 'Provides a network weight SCADA system',
    'category': 'SCADA/NWServer',
    'version': '17.0.0.1',
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'module_type': 'official',
    'data': [
        'security/nw_security.xml',
        'security/ir.model.access.csv',
        'data/type_of_controllers.xml',
        'views/menu.xml',
        'views/weight.xml',
        'views/errors.xml',
        'views/controllers.xml',
        'views/moxa.xml',
        'views/weight_dashboard.xml',
        'views/nw_config_settings.xml',
        'views/actions.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'nw_server/static/src/**/*',
        ],
    },
    'depends': [
        'base', 'web', 'board',
    ],
}
