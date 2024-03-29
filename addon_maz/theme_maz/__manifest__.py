{
    'name': 'MazUA Theme',
    'description': 'MAZ Website Theme',
    'category': 'Theme',
    'sequence': 10,
    'version': '1.0',
    'depends': ['website', 'website_sale'],
    'data': [
        'views/templates.xml',
        'data/images.xml',
        'views/header.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_maz/static/src/scss/styles.scss',
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
