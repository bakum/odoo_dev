{
    "name": "Regulatory Reporting Converter (XML to XLS)",
    "version": "1.0",
    "author": "Bakum Viacheslav",
    "category": "Tools",
    "depends": ["base", "web"],
    "assets": {
        "web.assets_backend": [
            "xml_to_xls/static/lib/xlsx.full.min.js",
            # "xml_to_xls/static/lib/handsontable.full.min.js",
            # "xml_to_xls/static/lib/handsontable.min.css",
            "xml_to_xls/static/src/js/xml_preview.xml",
            "xml_to_xls/static/src/js/xls_preview.js",
            # 'xml_to_xls/static/src/js/xls_preview_simple.js',
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/xls_template_views.xml",
        "views/xml_import_views.xml",
        "views/res_partner.xml",
        "report/report.xml",
    ],
    "installable": True,
    "application": True,
}
