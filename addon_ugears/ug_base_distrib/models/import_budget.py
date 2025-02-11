import base64

import xlrd

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class UgImportBudget(models.Model):
    _name = 'ug.distrib.import.budget'
    _description = 'Import distributor budget from xls'

    def _default_name(self):
        return _('Please load the xlsx file')

    def _default_distrib(self):
        return self.env.user.distrib_id

    name = fields.Char('Name', default=_default_name)
    xls_file = fields.Binary(string='Excel file', required=True)
    xls_filename = fields.Char(string='Excel Filename')
    products_ids = fields.One2many('ug.distrib.import.budget.list', 'wizard_id')
    distrib_id = fields.Many2one('distrib.distributors', 'Distributor', required=True, default=_default_distrib)
    len_products = fields.Integer(compute='get_len_products')

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
            if counter > 2:
                value = value.replace(',', '.')
                try:
                    value = float(value)
                except ValueError:
                    value = 0
            new_data.append(value)
        return new_data

    def _product_dict(self, data):
        data_array = self._validate_array(data)
        ProductRec = self.env['product.product']
        empty_record = {
            'product_id': ProductRec,
            'description': data_array[2],
            'barcode': data_array[0],
            'name': data_array[2],
            'default_code': data_array[1],
            'product_uom_qty': 0,
            'product_uom_qty2': 0,
            'product_uom_qty3': 0,
            'product_uom_qty4': 0,
            'product_uom_qty5': 0,
            'product_uom_qty6': 0,
            'product_uom_qty7': 0,
            'product_uom_qty8': 0,
            'product_uom_qty9': 0,
            'product_uom_qty10': 0,
            'product_uom_qty11': 0,
            'product_uom_qty12': 0,
        }
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
            return {
                'product_id': product.id,
                'description': data_array[2],
                'barcode': barcode,
                'name': data_array[2],
                'default_code': data_array[1],
                'product_uom_qty': data_array[3],
                'product_uom_qty2': data_array[4],
                'product_uom_qty3': data_array[5],
                'product_uom_qty4': data_array[6],
                'product_uom_qty5': data_array[7],
                'product_uom_qty6': data_array[8],
                'product_uom_qty7': data_array[9],
                'product_uom_qty8': data_array[10],
                'product_uom_qty9': data_array[11],
                'product_uom_qty10': data_array[12],
                'product_uom_qty11': data_array[13],
                'product_uom_qty12': data_array[14],
            }
        return empty_record

    def load_budget_from_xls(self):
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
                if sheet.name in ['Distr Budget']:
                    for row in range(sheet.nrows):
                        if row >= 1:
                            row_values = sheet.row_values(row)
                            vals = self._product_dict(row_values)
                            # if not vals['expense_total']:
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
            'name': _('Import budget'),
            'res_model': 'ug.distrib.import.budget',
            'view_mode': 'form',
            'res_id': self.id,
            'context': {
                'default_name': self.name,
                'default_xls_file': self.xls_file,
                'default_xls_filename': self.xls_filename,
                'default_distrib_id': self.distrib_id,
                'default_products_ids': self.products_ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def save_budget(self):
        year = self.date.strftime("%Y")
        BudgetRec = self.env['distrib.budget.move']
        domain = [('year', '=', year), ('distrib_id', '=', self.distrib_id.id)]
        budget = BudgetRec.search(domain)[:1]
        if not budget:
            budget = BudgetRec.create({
                'distrib_id': self.distrib_id.id,
                'date': self.date,
            })
        if budget:
            # product = []
            if budget.state == 'done':
                raise UserError(_('You can not edit the budget if is done. \n%s.') % budget.display_name)
            for row in self.products_ids:
                BudgetRecLine = self.env['distrib.budget.move.line']
                domain = [('move_id', '=', budget.id), ('product_id', '=', row.product_id.id)]
                product = BudgetRecLine.search(domain)[:1]
                if product:
                    val = {
                        # 'product_id': row.product_id,
                        'product_uom_qty': row.product_uom_qty,
                        'product_uom_qty2': row.product_uom_qty2,
                        'product_uom_qty3': row.product_uom_qty3,
                        'product_uom_qty4': row.product_uom_qty4,
                        'product_uom_qty5': row.product_uom_qty5,
                        'product_uom_qty6': row.product_uom_qty6,
                        'product_uom_qty7': row.product_uom_qty7,
                        'product_uom_qty8': row.product_uom_qty8,
                        'product_uom_qty9': row.product_uom_qty9,
                        'product_uom_qty10': row.product_uom_qty10,
                        'product_uom_qty11': row.product_uom_qty11,
                        'product_uom_qty12': row.product_uom_qty12,
                    }
                    product.update(val)
                # product.append((6, 0, val))


class UgImportBudgetList(models.TransientModel):
    _name = "ug.distrib.import.budget.list"
    _description = "Products list"
    _order = 'name'

    wizard_id = fields.Many2one('ug.distrib.import.budget', ondelete='cascade')
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
    product_uom_qty = fields.Float(
        string="January",
        digits='Product Unit of Measure', default=0.0,
    )
    product_uom_qty2 = fields.Float(
        string="February",
        digits='Product Unit of Measure', default=0.0,
    )
    product_uom_qty3 = fields.Float(
        string="March",
        digits='Product Unit of Measure', default=0.0,
    )
    product_uom_qty4 = fields.Float(
        string="April",
        digits='Product Unit of Measure', default=0.0,
    )
    product_uom_qty5 = fields.Float(
        string="May",
        digits='Product Unit of Measure', default=0.0,
    )
    product_uom_qty6 = fields.Float(
        string="June",
        digits='Product Unit of Measure', default=0.0,
    )
    product_uom_qty7 = fields.Float(
        string="July",
        digits='Product Unit of Measure', default=0.0,
    )
    product_uom_qty8 = fields.Float(
        string="August",
        digits='Product Unit of Measure', default=0.0,
    )
    product_uom_qty9 = fields.Float(
        string="September",
        digits='Product Unit of Measure', default=0.0,
    )
    product_uom_qty10 = fields.Float(
        string="October",
        digits='Product Unit of Measure', default=0.0,
    )
    product_uom_qty11 = fields.Float(
        string="November",
        digits='Product Unit of Measure', default=0.0,
    )
    product_uom_qty12 = fields.Float(
        string="December",
        digits='Product Unit of Measure', default=0.0,
    )
    barcode = fields.Char('Barcode')
    default_code = fields.Char('Default code')
    description = fields.Char('Description')

    @api.depends('product_id')
    def _compute_product_template_id(self):
        for line in self:
            line.product_template_id = line.product_id.product_tmpl_id

    def _search_product_template_id(self, operator, value):
        return [('product_id.product_tmpl_id', operator, value)]
