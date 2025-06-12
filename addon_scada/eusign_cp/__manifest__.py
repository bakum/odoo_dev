{
    'name': 'EUSignCP Connector',
    'author' : 'Bakum Viacheslav',
    'website' : 'https://optimus.com.ua',
    'summary' : 'EUSignCP Connector',
    'category': 'SCADA/NWServer',
    'version': '17.0.0.1',
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
            # ('include', 'web._assets_helpers'),
            ('include', 'web.assets_frontend'),
            # 'web/static/src/scss/pre_variables.scss',
            # 'web/static/lib/bootstrap/scss/_variables.scss',
            # ('include', 'web._assets_bootstrap_backend'),
            # ('include', 'web._assets_bootstrap'),  # Подключение Bootstrap
            #
            # # required for fa icons
            # 'web/static/src/libs/fontawesome/css/font-awesome.css',
            #
            # # include base files from framework
            # ('include', 'web._assets_core'),

            # 'web/static/src/core/utils/functions.js',
            # 'web/static/src/core/browser/browser.js',
            # 'web/static/src/core/registry.js',
            # 'web/static/src/core/assets.js',
            'eusign_cp/static/src/main.js',
            'eusign_cp/static/src/signer.js',
            'eusign_cp/static/src/signer.xml',
            'eusign_cp/static/src/helpers/signable.js',
            'eusign_cp/static/src/components/signer/eusigner.js',
            'eusign_cp/static/src/components/signer/eusigner.xml',
            'eusign_cp/static/src/components/verifier/verifier.js',
            'eusign_cp/static/src/components/verifier/verifier.xml',
            'eusign_cp/static/src/components/downloader/downloader.js',
            'eusign_cp/static/src/components/downloader/downloader.xml',
            'eusign_cp/static/src/components/downloader/downloader.css',
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
            'eusign_cp/static/src/signer.css',
        ]
    },
    'depends': ['base', 'web', "website"],
}