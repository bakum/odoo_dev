{
    'name': 'Distribution Base',
    'author' : 'Bakum Viacheslav',
    'website' : 'https://ugears.ua',
    'summary' : 'Provides a base for adding distribution support to models',
    'category': 'Sales/Distribution Management',
    'version': '16.0.0.1',
    'license' : 'LGPL-3',
    'installable': True,
    'application': True,
    'data' : [
        'security/distrib_security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/actions.xml',
        'views/menu.xml',
        'views/distrib.xml',
        'views/currency_views.xml',
        'views/product_public.xml',
        'views/product_category.xml',
        'views/pricelist_view.xml',
        'views/user_view.xml',
    ],
    'depends': [
        'base',
        'product',
        'stock'
    ],
}
