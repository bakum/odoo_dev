import base64
# import threading

import xlrd

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import float_compare


class UgImportInventory(models.TransientModel):
    _name = "ug.distrib.import.inventory"
    _description = "Import distributor inventory from xls"

    def _default_name(self):
        return _('Please load the xlsx file')

    def _default_distrib(self):
        return self.env.user.distrib_id

    name = fields.Char('Name', default=_default_name)
    xls_file = fields.Binary(string='Excel file', required=True)
    xls_filename = fields.Char(string='Excel Filename')
    products_ids = fields.One2many(
        'ug.distrib.import.inventory.list', 'wizard_id')
    distrib_id = fields.Many2one(
        'distrib.distributors', 'Distributor', required=True, default=_default_distrib)
    len_products = fields.Integer(compute='get_len_products')
    total_qtt = fields.Float(string='Total quantity',
                             compute='_compute_amounts')

    @api.depends('products_ids.qtt')
    def _compute_amounts(self):
        for order in self:
            # order_lines = order.move_line.filtered(lambda x: not x.display_type)
            order_lines = order.products_ids
            amount_untaxed = sum(order_lines.mapped('qtt'))

            order.total_qtt = amount_untaxed

    date = fields.Datetime(
        string="Date",
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
            value = value.replace(' ', '')
            if counter == 3:
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
        empty_record = {'product_id': ProductRec, 'description': 'Product Not found', 'qtt': data_array[3],
                        'barcode': data_array[0],
                        'name': data_array[2], 'default_code': data_array[1]}
        barcode = data_array[0]
        art = data_array[1]

        if barcode and art:
            domain = ['&', ('barcode', '=', barcode),
                      ('default_code', '=', art)]
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

    def load_inventory_from_xls(self):
        try:
            file_data = base64.b64decode(self.xls_file)
            book = xlrd.open_workbook(file_contents=file_data)
        except FileNotFoundError:
            raise UserError(
                'No such file or directory found. \n%s.' % self.xls_filename)
        except xlrd.biffh.XLRDError:
            raise UserError('Only excel files are supported.')

        products = []
        self.products_ids.unlink()
        for sheet in book.sheets():
            try:
                if sheet.name in ['Distr Inventory']:
                    for row in range(sheet.nrows):
                        if row >= 1:
                            row_values = sheet.row_values(row)
                            vals = self._get_product_dict(row_values)
                            # if not vals['qtt']:
                            #     continue
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
            'name': _('Import inventory'),
            'res_model': 'ug.distrib.import.inventory',
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

    def _get_inventory_move_values(self, out=False, date=None):
        # self.ensure_one()
        # if fields.Float.is_zero(qty, 0, precision_rounding=0.01):
        #     name = _('Product Quantity Confirmed')
        # else:
        #     name = _('Product Quantity Updated')

        return {
            'name': self.env.context.get('inventory_name'),
            'distrib_id': self.distrib_id.id,
            'state': 'draft',
            'is_inventory': True,
            'operation': 'out' if out else 'inc',
            'date_order': date if date else fields.Datetime.now(),
            # 'move_line': [(0, 0, {
            #     'product_id': product_id.id,
            #     # 'product_uom_id': product_uom_id.id,
            #     'distrib_id': self.distrib_id.id,
            #     'product_uom_qty': qty,
            #     'operation': 'out' if out else 'inc',
            # })]
        }

    def _save_inventory(self):
        QuantHistory = self.env['distrib.quant.history'].sudo()
        move_out = []
        move_in = []
        product_ids = []
        for products in self.products_ids:
            if not products.product_id:
                continue
            product_ids.append(products.product_id.id)
            # move_vals = []
            qtt_on_date = QuantHistory.balance_product_on_date(
                products.product_id, self.distrib_id, self.date)
            if products.qtt != qtt_on_date:
                qtt = products.qtt - qtt_on_date
                if float_compare(qtt, 0, precision_rounding=0.01) > 0:
                    # move_vals.append(
                    #     self._get_inventory_move_values(product_id=products.product_id, qty=qtt, date=self.date))
                    move_in.append((0, 0, {
                        'product_id': products.product_id.id,
                        'name': products.product_id.get_product_multiline_description_sale(),
                        # 'product_uom_id': product_uom_id.id,
                        'distrib_id': self.distrib_id.id,
                        'product_uom_qty': qtt,
                        'operation': 'inc',
                    }))
                elif float_compare(qtt, 0, precision_rounding=0.01) < 0:
                    # move_vals.append(self._get_inventory_move_values(product_id=products.product_id, qty=-qtt, out=True,
                    #                                                  date=self.date))
                    move_out.append((0, 0, {
                        'product_id': products.product_id.id,
                        'name': products.product_id.get_product_multiline_description_sale(),
                        # 'product_uom_id': product_uom_id.id,
                        'distrib_id': self.distrib_id.id,
                        'product_uom_qty': -qtt,
                        'operation': 'out',
                    }))
                else:
                    return
        moves = self.env['distrib.distributors.move']
        if len(move_out) > 0:
            move_vals = self._get_inventory_move_values(
                out=True, date=self.date)
            res = moves.with_context(inventory_mode=False).create(move_vals)
            res.move_line = move_out
            res.action_done()
        if len(move_in) > 0:
            move_vals = self._get_inventory_move_values(date=self.date)
            res = moves.with_context(inventory_mode=False).create(move_vals)
            res.move_line = move_in
            res.action_done()

        Quants = self.env['distrib.quant'].sudo()
        domain = ['&', ('distrib_id', '=', self.distrib_id.id),
                  ('product_id', 'not in', product_ids)]
        quants_so = Quants.search(domain)
        move_out = []
        move_in = []
        for quant in quants_so:
            qtt_on_date = QuantHistory.balance_product_on_date(
                quant.product_id, self.distrib_id, self.date)
            if float_compare(qtt_on_date, 0, precision_rounding=0.01) > 0:
                move_out.append((0, 0, {
                    'product_id': quant.product_id.id,
                    'name': quant.product_id.get_product_multiline_description_sale(),
                    # 'product_uom_id': product_uom_id.id,
                    'distrib_id': self.distrib_id.id,
                    'product_uom_qty': qtt_on_date,
                    'operation': 'out',
                }))
            elif float_compare(qtt_on_date, 0, precision_rounding=0.01) < 0:
                move_in.append((0, 0, {
                    'product_id': quant.product_id.id,
                    'name': quant.product_id.get_product_multiline_description_sale(),
                    # 'product_uom_id': product_uom_id.id,
                    'distrib_id': self.distrib_id.id,
                    'product_uom_qty': -qtt_on_date,
                    'operation': 'inc',
                }))    
        if len(move_out) > 0:
            move_vals = self._get_inventory_move_values(
                out=True, date=self.date)
            res = moves.with_context(inventory_mode=False).create(move_vals)
            res.move_line = move_out
            res.action_done()
        if len(move_in) > 0:
            move_vals = self._get_inventory_move_values(date=self.date)
            res = moves.with_context(inventory_mode=False).create(move_vals)
            res.move_line = move_in
            res.action_done()    

        # threaded_calculation = threading.Thread(
        #     target=moves._run_recalculate_job)
        # threaded_calculation.start()
        moves._run_recalculate_job()

    def save_inventory(self):
        date_in_the_past = self.date.date() < fields.Datetime.today().date()
        if date_in_the_past:
            if self.env.user.has_group('ug_base_distrib.group_distrib_user') and not self.env.user.has_group(
                    'ug_base_distrib.group_distrib_manager'):
                raise AccessError(
                    "You do not have access rights to make inventory in the past.")
            return self._save_inventory()
        Quants = self.env['distrib.quant'].sudo()
        # domain = [('distrib_id', '=', self.distrib_id)]
        # quants_so = Quants.search(domain)
        product_ids = []
        for products in self.products_ids:
            if not products.product_id:
                continue
            product_ids.append(products.product_id.id)
            domain = [('product_id', '=', products.product_id.id)]
            domain = expression.AND([
                domain,
                [('distrib_id', '=', self.distrib_id.id)]
            ])
            quants_so = Quants.search(domain)
            if quants_so:
                for quant in quants_so:
                    if products.qtt != quant.quantity:
                        quant.inventory_quantity = products.qtt
                        quant.import_date = self.date
                        quant.action_apply_inventory()
            else:
                value = {
                    'distrib_id': self.distrib_id.id,
                    'product_id': products.product_id.id,
                    'quantity': 0,
                    'inventory_quantity': 0,
                    'in_date': self.date,
                    'import_date': self.date
                }
                quant_new = Quants.create(value)
                quant_new.inventory_quantity = products.qtt
                quant_new.action_apply_inventory()

        domain = ['&', ('distrib_id', '=', self.distrib_id.id),
                  ('product_id', 'not in', product_ids)]
        quants_so = Quants.search(domain)
        for quant in quants_so:
            if quant.quantity != 0:
                quant.inventory_quantity = 0.0
                quant.action_apply_inventory()


class UgImportInventoryList(models.TransientModel):
    _name = "ug.distrib.import.inventory.list"
    _description = "Products list"
    _order = 'name'

    wizard_id = fields.Many2one(
        'ug.distrib.import.inventory', ondelete='cascade')
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
