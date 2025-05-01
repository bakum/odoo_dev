{
    'name': 'Rest API connector for 1C:Enterprise',
    'author': 'Bakum Viacheslav',
    'website': 'https://ugears.ua',
    'summary': 'Rest API connector for 1C:Enterprise',
    'category': 'Sales/Distribution Management',
    'version': '16.0.0.1',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'product',
        'ug_base_distrib',
    ],
    "data": [
        # Security
        'security/groups.xml',
        'security/ir.model.access.csv',
        # Views
        'views/api_rest_version_views.xml',
        'views/api_rest_path_views.xml',
        'views/api_rest_tag_views.xml',
        'views/api_rest_log_views.xml',
        'views/swagger_templates.xml',
    ],
    'assets': {
        'ug_1c_connector.assets_swagger': [
            'ug_1c_connector/static/lib/swagger-ui-3.38.0/swagger-ui.css',
            'ug_1c_connector/static/lib/swagger-ui-3.38.0/swagger-ui-bundle.js',
            'ug_1c_connector/static/lib/swagger-ui-3.38.0/swagger-ui-standalone-preset.js',
        ],
    },

    # "external_dependencies": {
    #     "python": ["pydantic"]
    # },
}
