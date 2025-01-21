import base64

import xlrd

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError

CHANNEL_MAP = {
    0: 'Channel_0001',
    1: 'Channel_0002',
    2: 'Channel_0003',
    3: 'Channel_0004',
    4: 'Channel_0005',
}

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
        string="Operation")
    date_order = fields.Datetime(
        string="Operation Date",
        required=True, readonly=False,
        default=fields.Datetime.now)

    # @api.onchange('xls_filename')
    # def _onchange_xls_filename(self):
    #     self.products_ids.unlink()
    def _prepare_move_value(self):
        values = {
            'operation': self.operation,
            'distrib_id': self.distrib_id.id,
            # 'channel_id': self.channel_id,
            'user_id': self.env.user.id,
            'date_order': self.date_order,
            # 'website_id': self.id,
        }
        return values

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
            value = value.replace(' ', '')
            if counter >= 3:
                value = value.replace(',', '.')
                try:
                    value = int(float(value))
                except ValueError:
                    value = 0
            new_data.append(value)
        return new_data

    def rearrage_array(self, data):
        array_of_data = []
        new_data = data[0:4]
        array_of_data.append(new_data)
        for counter, row in enumerate(data):
            app_data = new_data[0:3]
            if counter > 3:
                app_data.append(row)
                array_of_data.append(app_data)
        return array_of_data

    def get_id_from_ext_id(self, ext_id):
        ext = self.env['ir.model.data'].sudo().search([('name', '=', ext_id)], limit=1)
        id = False
        if len(ext) > 0:
            for line in ext:
                id = line.res_id
        return ext_id if not id else id

    def _get_product_list(self, data_array):
        array_for_product = []
        data_array = self._validate_array(data_array)
        data_array = self.rearrage_array(data_array)
        for counter, row in enumerate(data_array):
            new_dict = self._get_product_dict(row)
            if len(data_array) > 1:
                new_dict['channel_id'] = self.get_id_from_ext_id(CHANNEL_MAP[counter])
            array_for_product.append(new_dict)
        return array_for_product

    def _get_product_dict(self, data_array):
        # data_array = self._validate_array(data_array)
        ProductRec = self.env['product.product']
        # ChannelRec = self.env['distrib.sales.channels']
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
                if sheet.name == 'Distr Sales' or sheet.name == 'Distr Order':
                    for row in range(sheet.nrows):
                        if row >= 1:
                            row_values = sheet.row_values(row)
                            vals = self._get_product_list(row_values)
                            if len(vals) > 1:
                                self.operation = 'out'
                                self.channel_id = vals[0]['channel_id']
                            else:
                                self.operation = 'inc'

                            for val in vals:
                                if not val['qtt'] or val['qtt'] == 0:
                                    continue
                                products.append((0, 0, val))
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
            'name': _('Import move'),
            'res_model': 'ug.distrib.import.move',
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
        so_data = self._prepare_move_value()
        DistribMove = self.env['distrib.distributors.move'].sudo()
        move_sudo = DistribMove.with_user(SUPERUSER_ID).create(so_data)
        move_sudo = move_sudo.with_user(self.env.user).sudo()
        products = []
        for line in self.products_ids:
            if line.product_id:
                product = {
                    'product_id': line.product_id.id,
                    'channel_id': line.channel_id.id,
                    'name': line.product_id.display_name,
                    'product_uom_qty': line.qtt
                }
                products.append((0,0,product))
        move_sudo.move_line = products
        move_sudo.update({'channel_id': self.products_ids[0].channel_id.id})

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
