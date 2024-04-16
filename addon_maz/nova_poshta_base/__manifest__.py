{
    'name': 'Nova Poshta Base',
    'version': '17.0.0.1',
    'category': 'Inventory',
    'author': 'Bakum Viacheslav',
    'website': 'https://optimus.com.ua',
    'license': 'LGPL-3',
    'summary': """
        Integration with the Nova Poshta delivery service.
    """,
    'depends': [
        'product',
        'delivery',
    ],
    'data': [
        'security/ir.model.access.csv',
        # 'data/data.xml',
        # 'views/np_menu_views.xml',
        # 'views/np_config_views.xml',
        # 'views/np_area_views.xml',
        # 'views/np_warehouse_views.xml',
        # 'views/np_settlement_views.xml',
        # 'views/np_city_views.xml',
        # 'views/res_partner_views.xml',
    ],
    # 'external_dependencies': {
    #     'python': [
    #         'http',
    #         'json',
    #     ],
    # },
    'application': False,
    'installable': True,
    'auto_install': False,
}