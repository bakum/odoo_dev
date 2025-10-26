{
    'name': 'EUSign Authorization',
    'author' : 'Bakum Viacheslav',
    'website' : 'https://optimus.com.ua',
    'summary' : 'EUSign Authorization',
    'category': 'SCADA/NWServer',
    'version': '17.0.0.1',
    'license' : 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
    'depends': ['web'],
    'license': 'LGPL-3',
    'bootstrap': True,
    'data': [
        'views/login_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'sign_auth/static/lib/euutils.js',
            'sign_auth/static/lib/euscpt.js',
            'sign_auth/static/lib/euscpm.js',
            'sign_auth/static/lib/euscp.js',
            'sign_auth/static/lib/qr/qrcodedecode.js',
            'sign_auth/static/lib/qr/reedsolomon.js',
            'sign_auth/static/lib/fs/Blob.min.js',
            'sign_auth/static/lib/fs/FileSaver.js',
            'sign_auth/static/lib/fs/jszip.min.js',
            'sign_auth/static/lib/toastify-js.js',
            'sign_auth/static/lib/toastify.min.css',


            # 'sign_auth/static/src/js/cert_provider.js',
            'sign_auth/static/src/login/**/*',
            'sign_auth/static/src/scss/login.scss',
        ],
    },


}