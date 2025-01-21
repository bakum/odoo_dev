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

    def _validate_array(self, data):
        new_data = []
        for counter, row in enumerate(data):
            if counter == 2:
                new_data.append(row)
                continue
            try:
                value = str(int(row))
            except ValueError:
                value = str(row)
            value = value.replace(' ','')
            if counter >= 3:
                value = value.replace(',', '.')
                try:
                    value = int(float(value))
                except ValueError:
                    value = 0
            new_data.append(value)
        return new_data

    def _get_product_dict(self, data_array):
        data_array = self._validate_array(data_array)
        ProductRec = self.env['product.product']
        ChannelRec = self.env['distrib.sales.channels']
        empty_record = {'product_id': False, 'description': data_array[2], 'qtt': data_array[3],
                        'barcode': data_array[0], 'channel_id': False,
                        'name': data_array[2], 'default_code': data_array[1]}
        barcode = data_array[0]
        art = data_array[1]

        if barcode and art:
            domain = ['&', ('barcode', '=', barcode), ('default_code', '=', art)]
        elif barcode:
            domain = [('barcode', '=', barcode)]
        elif art:
            domain = [('default_code', '=', art)]
        else:
            return empty_record
        product = ProductRec.search(domain)[:1]
        if product:
            return {'product_id': product.id, 'description': data_array[2], 'qtt': data_array[3], 'barcode': barcode,
                    'name': data_array[2], 'default_code': data_array[1]}
        return empty_record

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

    def save_move(self):
        pass


class UgImportMoveList(models.TransientModel):
    _name = "ug.distrib.import.move.list"
    _description = "Products list"
    _order = 'name'

    def _default_channel(self):
        return self.wizard_id.channel_id.id

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
    channel_id = fields.Many2one(
        comodel_name='distrib.sales.channels',
        string="Sales Channel",
        default=_default_channel,
        readonly=False, index=True
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
