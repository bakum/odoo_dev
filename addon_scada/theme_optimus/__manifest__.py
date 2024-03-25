{
    'name': 'OptimusHome Theme',
    'description': 'Optimus website theme',
    'category': 'Theme',
    'sequence': 10,
    'version': '1.0',
    'depends': ['website'],
    'data': [
        'data/images.xml',
        'views/header.xml',
        'views/footer.xml',

    ],
    'assets': {
        'web._assets_primary_variables': [
            "theme_optimus/static/src/scss/primary_variables.scss",
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
