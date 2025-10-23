{
    'name': 'EUSignCP Connector',
    'author' : 'Bakum Viacheslav',
    'website' : 'https://optimus.com.ua',
    'summary' : 'EUSignCP Connector',
    'category': 'SCADA/NWServer',
    'version': '18.0.0.1',
    'license' : 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
    "data": [
        'views/signer_template.xml',
        'data/data.xml',
    ],
    'assets': {
        'eusign_cp.assets_signer': [
            # bootstrap
            'web/static/lib/bootstrap/dist/css/bootstrap.css',
            # required for fa icons
            'web/static/src/libs/fontawesome/css/font-awesome.css',
            #
            # include base files from framework
            'web/static/src/module_loader.js',
            # libs
            'web/static/lib/luxon/luxon.js',
            'web/static/lib/owl/owl.js',
            'web/static/lib/owl/odoo_module.js',
            'web/static/src/env.js',
            'web/static/src/session.js',
            'web/static/src/core/**/*.js',

            'eusign_cp/static/src/**/*',
        ],
        'eusign_cp.assets_library': [
            'eusign_cp/static/lib/euutils.js',
            'eusign_cp/static/lib/euscpt.js',
            'eusign_cp/static/lib/euscpm.js',
            'eusign_cp/static/lib/euscp.ex.js',
            'eusign_cp/static/lib/qr/qrcodedecode.js',
            'eusign_cp/static/lib/qr/reedsolomon.js',
            'eusign_cp/static/lib/fs/Blob.min.js',
            'eusign_cp/static/lib/fs/FileSaver.js',
            'eusign_cp/static/lib/fs/jszip.min.js',
            'eusign_cp/static/lib/toastify-js.js',
            'eusign_cp/static/lib/toastify.min.css',
        ]
    },
    'depends': ['base', 'web', "website"],
}