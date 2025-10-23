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

            # 'web/static/lib/jquery/jquery.js',
            # required for fa icons
            'web/static/src/libs/fontawesome/css/font-awesome.css',
            #
            # include base files from framework
            # ('include', 'web._assets_core'),

            'web/static/src/module_loader.js',
            # libs
            'web/static/lib/luxon/luxon.js',
            'web/static/lib/owl/owl.js',
            'web/static/lib/owl/odoo_module.js',
            'web/static/src/env.js',
            'web/static/src/session.js',
            'web/static/src/core/**/*.js',

            'eusign_cp/static/src/main.js',
            'eusign_cp/static/src/signer.js',
            'eusign_cp/static/src/signer.xml',
            'eusign_cp/static/src/signer.css',
            'eusign_cp/static/src/helpers/signable.js',
            'eusign_cp/static/src/components/**/*',
            'eusign_cp/static/src/accordion.css',
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