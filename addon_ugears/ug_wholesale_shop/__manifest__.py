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
        'views/distributors.xml',
        'views/import_order.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ug_wholesale_shop/static/src/js/website_sale_override.js',
            # ('replace', 'website_sale/static/src/js/website_sale.js', 'ug_wholesale_shop/static/src/js/website_sale.js'),
            ('replace', 'website_sale/static/src/js/website_sale_utils.js', 'ug_wholesale_shop/static/src/js/website_sale_utils.js'),
            'ug_wholesale_shop/static/src/js/variant_mixin.js',
            # 'ug_wholesale_shop/static/src/js/website_sale_override.js',
            'ug_wholesale_shop/static/src/js/wholesale_calculator.js',
        ],
        'web.assets_backend': [
            'ug_wholesale_shop/static/src/views/import_order_controller.js',
            'ug_wholesale_shop/static/src/views/import_order_view.js',
            'ug_wholesale_shop/static/src/views/import_order_button.xml',
        ],
    },
    "external_dependencies": {
        "python": ["rectpack"]
    },
}
