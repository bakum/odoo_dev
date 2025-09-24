from odoo import models, fields

class XlsTemplate(models.Model):
    _name = "xml.xls.template"
    _description = "XLS Template"

    name = fields.Char(required=True)
    template_file = fields.Binary("XLS Template", required=True)
    template_filename = fields.Char("Template Filename")
    report_type = fields.Selection([
        ("balance", "Balance"),
        ("bdds", "Cash flow"),
        ("profit_loss", "Profit and Loss"),
    ], required=True, default="balance")
