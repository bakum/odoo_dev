{
    'name': 'Import of NBU currency rates',
    'author': 'Bakum Viacheslav',
    'website': 'https://optimus.com.ua',
    'category': 'Sales/Utility',
    'version': '16.0.0.1',
    'license': 'LGPL-3',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/currency_views.xml',
        'views/res_currency_views.xml',
        'wizard/import_rates_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bv_import_rates_from_nbu/static/src/views/res_currency_list_controller.js',
            'bv_import_rates_from_nbu/static/src/views/res_currency_list_view.js',
            'bv_import_rates_from_nbu/static/src/views/res_currency_list.xml',
        ],
    },
    'application': True,
}
