{
    'name': 'Distribution''s Wholesale shop',
    'author': 'Bakum Viacheslav',
    'website': 'https://ugears.ua',
    'summary': 'Order your products online',
    'category': 'Sales/Distribution Management',
    'version': '16.0.0.1',
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'depends': [
        'ug_base_distrib',
        'website_sale'
    ],
    'data': [
        'views/templates.xml',
        'views/product_public.xml',
        'views/actions.xml',
        'views/menu.xml',
        'security/wholesale_security.xml',
        'security/ir.model.access.csv',
        'data/packages_sizes_data.xml',
        'views/packages_sizes.xml',
    ],
'assets': {
        'web.assets_frontend': [
            # 'sale/static/src/js/variant_mixin.js',
            # 'website_sale/static/src/js/variant_mixin.js',
            'ug_wholesale_shop/static/src/js/variant_mixin.js',
        ]
    }
}
