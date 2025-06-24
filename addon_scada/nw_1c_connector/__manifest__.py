{
    'name': 'Rest API connector for 1C:Enterprise',
    'author' : 'Bakum Viacheslav',
    'website' : 'https://optimus.com.ua',
    'summary' : 'Rest API connector for 1C:Enterprise',
    'category': 'SCADA/NWServer',
    'version': '18.0.0.1',
    'license' : 'LGPL-3',
    'depends': [
        'base',
        'nw_server',
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
        'nw_1c_connector.assets_swagger': [
            'nw_1c_connector/static/lib/swagger-ui-3.38.0/swagger-ui.css',
            'nw_1c_connector/static/lib/swagger-ui-3.38.0/swagger-ui-bundle.js',
            'nw_1c_connector/static/lib/swagger-ui-3.38.0/swagger-ui-standalone-preset.js',
        ],
    },
}
