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
        'views/menu.xml',
        'security/wholesale_security.xml',
    ]
}
