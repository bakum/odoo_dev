import base64

import xlrd

from odoo import models, fields, _, api
from odoo.exceptions import UserError
from odoo.http import request


class UgImportOrder(models.TransientModel):
    _name = "ug.wholesale.import.order"
    _description = "Import order from xls"

    def _default_name(self):
        return _('Please load the xlsx file')

    name = fields.Char('Name', default=_default_name)
    xls_file = fields.Binary(string='Excel file', required=True)
    xls_filename = fields.Char(string='Excel Filename')
    products_ids = fields.One2many('ug.wholesale.import.order.list', 'wizard_id')

    def write(self, vals):
        result = super(UgImportOrder, self).write(vals)

        return result

    @api.onchange('xls_filename')
    def _onchange_type(self):
        if self.xls_filename:
            self.load_order_from_xls()

    def _get_product_dict(self, data_array):
        ProductRec = self.env['product.product']
        try:
            barcode = str(int(data_array[0]))
        except ValueError:
            barcode = str(data_array[0])

        domain = [('barcode', '=', barcode)]
        product = ProductRec.search(domain)[:1]
        if product:
            return {'product_id': product, 'description': data_array[1], 'qtt': data_array[2], 'barcode': barcode,
                    'name': data_array[1]}
        return {'product_id': ProductRec, 'description': data_array[1], 'qtt': data_array[2], 'barcode': barcode,
                'name': data_array[1]}

    def load_order_from_xls(self):
        # sale_order_id = request.session.get('sale_order_id')
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
            try:
                if sheet.name == 'Distr Order':
                    for row in range(sheet.nrows):
                        if row >= 1:
                            row_values = sheet.row_values(row)
                            vals = self._get_product_dict(row_values)
                            if not vals['qtt'] or vals['qtt'] == 0:
                                continue
                            products.append((0, 0, vals))
            except IndexError:
                pass
        try:
            self.products_ids = products
            if not products:
                self.name = _("Nothing to load")
            else:
                self.name = _("Successfully loaded")
        except ValueError:
            self.name = _("Wrong format of file")
        # return {
        #     'name': _('Imported order'),
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'sale.order',
        #     'view_mode': 'tree,kanban,activity',
        #     'domain': [('website_id', '!=', False)],
        #     'context': {
        #         'active_ids': self._context.get('active_ids'),
        #     },
        # }


class UgImportOrderList(models.TransientModel):
    _name = "ug.wholesale.import.order.list"
    _description = "Products list"
    _order = 'name'

    wizard_id = fields.Many2one('ug.wholesale.import.order')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product",
        change_default=True, ondelete='restrict', index='btree_not_null',
        required=True,
        domain="[('sale_ok', '=', True)]")

    product_template_id = fields.Many2one(
        string="Product Template",
        comodel_name='product.template',
        compute='_compute_product_template_id',
        readonly=False,
        search='_search_product_template_id',
        # previously related='product_id.product_tmpl_id'
        # not anymore since the field must be considered editable for product configurator logic
        # without modifying the related product_id when updated.
        domain=[('sale_ok', '=', True)])
    name = fields.Char('Name', readonly=True)
    qtt = fields.Float('Quantity', digits=(12, 1))
    qtt_by_box = fields.Float('Quantity by boxes', compute='_compute_product_by_box', store=True)
    barcode = fields.Char('Barcode')
    description = fields.Char('Description')

    @api.depends('qtt','product_id')
    def _compute_product_by_box(self):
        for line in self:
            package = 0 if line.product_id.qty_in_cartoon == 0 else line.qtt // line.product_id.qty_in_cartoon
            package_float = 0 if line.product_id.qty_in_cartoon == 0 else line.qtt / line.product_id.qty_in_cartoon
            if package_float > package:
                package += 1
            line.qtt_by_box = package * line.product_id.qty_in_cartoon

    @api.depends('product_id')
    def _compute_product_template_id(self):
        for line in self:
            line.product_template_id = line.product_id.product_tmpl_id

    def _search_product_template_id(self, operator, value):
        return [('product_id.product_tmpl_id', operator, value)]
