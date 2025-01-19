import base64

import xlrd

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class UgImportMove(models.TransientModel):
    _name = "ug.distrib.import.move"
    _description = "Import distributor move from xls"

    def _default_name(self):
        return _('Please load the xlsx file')

    def _default_distrib(self):
        return self.env.user.distrib_id

    name = fields.Char('Name', default=_default_name)
    xls_file = fields.Binary(string='Excel file', required=True)
    xls_filename = fields.Char(string='Excel Filename')
    products_ids = fields.One2many('ug.distrib.import.move.list', 'wizard_id')
    distrib_id = fields.Many2one('distrib.distributors', 'Distributor', required=True, default=_default_distrib)
    channel_id = fields.Many2one(comodel_name='distrib.sales.channels', string="Sales Channel")
    len_products = fields.Integer(compute='get_len_products')
    operation = fields.Selection(
        selection=[
            ('inc', _("Income")),
            ('out', _("Expenses")),
        ],
        required=True,
        string="Operation")
    date_order = fields.Datetime(
        string="Operation Date",
        required=True, readonly=False,
        default=fields.Datetime.now)

    @api.depends('products_ids')
    def get_len_products(self):
        self.len_products = len(self.products_ids)


    def load_move_from_xls(self):
        try:
            file_data = base64.b64decode(self.xls_file)
            book = xlrd.open_workbook(file_contents=file_data)
        except FileNotFoundError:
            raise UserError('No such file or directory found. \n%s.' % self.xls_filename)
        except xlrd.biffh.XLRDError:
            raise UserError('Only excel files are supported.')

        products = []
        self.products_ids.unlink()
        for sheet in book.sheets():
            pass

    def save_move(self):
        pass


class UgImportMoveList(models.TransientModel):
    _name = "ug.distrib.import.move.list"
    _description = "Products list"
    _order = 'name'

    wizard_id = fields.Many2one('ug.distrib.import.move', ondelete='cascade')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product")

    product_template_id = fields.Many2one(
        string="Product Template",
        comodel_name='product.template',
        compute='_compute_product_template_id',
        readonly=False,
        search='_search_product_template_id',
        # previously related='product_id.product_tmpl_id'
        # not anymore since the field must be considered editable for product configurator logic
        # without modifying the related product_id when updated.
    )
    name = fields.Char('Name', readonly=True)
    qtt = fields.Float('Quantity', digits=(12, 1))
    barcode = fields.Char('Barcode')
    default_code = fields.Char('Default code')
    description = fields.Char('Description')

    @api.depends('product_id')
    def _compute_product_template_id(self):
        for line in self:
            line.product_template_id = line.product_id.product_tmpl_id

    def _search_product_template_id(self, operator, value):
        return [('product_id.product_tmpl_id', operator, value)]
