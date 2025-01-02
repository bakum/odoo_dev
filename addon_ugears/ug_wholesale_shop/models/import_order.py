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

    def _default_distrib(self):
        return self.env.user.distrib_id

    name = fields.Char('Name', default=_default_name)
    xls_file = fields.Binary(string='Excel file', required=True)
    xls_filename = fields.Char(string='Excel Filename')
    products_ids = fields.One2many('ug.wholesale.import.order.list', 'wizard_id')
    distrib_id = fields.Many2one('distrib.distributors', 'Distributor', required=True, default=_default_distrib)

    def _prepare_order_value(self):
        values = {
            'company_id': self.env.company.id,

            # 'fiscal_position_id': fiscal_position_id,
            'partner_id': self.distrib_id.partner_id.id,
            'partner_invoice_id': self.distrib_id.partner_id.id,
            # 'partner_shipping_id': addr['delivery'],

            'pricelist_id': self.distrib_id.pricelist_id,
            # 'payment_term_id': self.sale_get_payment_term(partner_sudo),

            'team_id': self.distrib_id.partner_id.parent_id.team_id.id or self.distrib_id.partner_id.team_id.id,
            'user_id': self.env.user.id,
            # 'website_id': self.id,
        }
        return values

    def write(self, vals):
        result = super(UgImportOrder, self).write(vals)

        # SaleOrder = self.env['sale.order'].sudo()
        # so_data = self._prepare_order_value()
        # sale_order_sudo = SaleOrder.with_user(self.env.user).create(so_data)
        #
        # for line in self.products_ids:
        #     pass

        return result

    # @api.onchange('xls_filename')
    # def _onchange_type(self):
    #     if self.xls_filename:
    #         self.load_order_from_xls()

    def _get_product_dict(self, data_array):
        ProductRec = self.env['product.product']
        try:
            barcode = str(int(data_array[0]))
        except ValueError:
            barcode = str(data_array[0])

        domain = [('barcode', '=', barcode)]
        product = ProductRec.search(domain)[:1]
        if product:
            return {'product_id': product.id, 'description': data_array[1], 'qtt': data_array[2], 'barcode': barcode,
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
        # self.products_ids.unlink()
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
        return {
            'name': _('Import order'),
            'res_model': 'ug.wholesale.import.order',
            'view_mode': 'form',
            'res_id': self.id,
            'context': {
                'default_name': self.name,
                'default_xls_file': self.xls_file,
                'default_xls_filename': self.xls_filename,
                'default_distrib_id': self.distrib_id,
                'default_products_ids': self.products_ids,
                # 'active_ids': self._context.get('active_ids'),
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def save_order(self):
        pass


class UgImportOrderList(models.TransientModel):
    _name = "ug.wholesale.import.order.list"
    _description = "Products list"
    _order = 'name'

    wizard_id = fields.Many2one('ug.wholesale.import.order',ondelete='cascade')
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
    qtt_by_box = fields.Float('Quantity by boxes', compute='_compute_product_by_box', store=True)
    barcode = fields.Char('Barcode')
    description = fields.Char('Description')

    @api.depends('qtt', 'product_id')
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
