{
    'name': 'Import of NBU currency rates',
    'author' : 'Bakum Viacheslav',
    'website' : 'https://ugears.ua',
    'category': 'Sales/Distribution Management',
    'version': '17.0.0.1',
    'license' : 'LGPL-3',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_currency_views.xml',
        'wizard/import_rates_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ug_import_rates_from_nbu/static/src/views/res_currency_list_controller.js',
            'ug_import_rates_from_nbu/static/src/views/res_currency_list_view.js',
            'ug_import_rates_from_nbu/static/src/views/res_currency_list.xml',
        ],
    },
    'application': True,
}
