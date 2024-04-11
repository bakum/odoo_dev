{
    'name': 'MazUA Theme',
    'description': 'MAZ Website Theme',
    'category': 'Theme',
    'sequence': 10,
    'version': '1.0',
    'depends': ['website', 'website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/divisions.xml',
        'views/partner_view.xml',
        # 'views/templates.xml',
        'data/images.xml',
        # 'views/header.xml',
        # 'views/website_template.xml',
        # 'views/portal_my_home.xml',
        # 'views/homepage.xml',
        # 'views/contactus.xml',
        # 'views/aboutus.xml',
        # 'views/payment_and_delivery.xml',
        # 'views/products.xml',
        # 'views/product.xml',
        'views/snippets/categories.xml',
        'views/snippets/snippets.xml',
        'views/pricelist_view.xml',
        'views/product_public.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_maz/static/src/scss/styles.scss',
            # 'theme_maz/static/src/js/main.js',
        ],
        'web._assets_primary_variables': [
            "theme_maz/static/src/scss/primary_variables.scss",
        ]
    },
    'images': [
    ],
    'snippet_lists': {
    },
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
