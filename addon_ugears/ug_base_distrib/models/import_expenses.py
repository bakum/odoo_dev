import base64

import xlrd

from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import UserError

COSTS_MAP = {
    1: 'type_4',
    2: 'type_5',
    3: 'type_6',
    4: 'type_1',
    5: 'type_2',
    6: 'type_3',
}


class UgImportExpenses(models.Model):
    _name = 'ug.distrib.import.expenses'
    _description = 'Import distributor expenses from xls'

    def _default_name(self):
        return _('Please load the xlsx file')

    def _default_distrib(self):
        return self.env.user.distrib_id

    name = fields.Char('Name', default=_default_name)
    xls_file = fields.Binary(string='Excel file', required=True)
    xls_filename = fields.Char(string='Excel Filename')
    currency_id = fields.Many2one(
        related='distrib_id.pricelist_id.currency_id',
        store=True, index=True, precompute=True)
    expenses_ids = fields.One2many(
        comodel_name='ug.distrib.import.expenses.list',
        inverse_name='wizard_id')
    distrib_id = fields.Many2one('distrib.distributors', 'Distributor', required=True, default=_default_distrib)
    len_expenses = fields.Integer(compute='get_len_expenses')

    date = fields.Datetime(
        string="Date",
        required=True, readonly=False,
        default=fields.Datetime.now)

    @api.depends('expenses_ids')
    def get_len_expenses(self):
        self.len_expenses = len(self.expenses_ids)

    def get_id_from_ext_id(self, ext_id):
        if not ext_id:
            return False
        ext = self.env['ir.model.data'].sudo().search([('name', '=', ext_id)], limit=1)
        id = False
        if len(ext) > 0:
            for line in ext:
                id = line.res_id
        return ext_id if not id else id

    def _validate_array(self, data):
        new_data = []
        for counter, row in enumerate(data):
            if counter < 2:
                new_data.append(row)
                continue
            try:
                value = str(int(row))
            except ValueError:
                value = str(row)
            value = value.replace(' ', '')
            if counter == 2:
                value = value.replace(',', '.')
                try:
                    value = float(value)
                except ValueError:
                    value = 0
            new_data.append(value)
        return new_data

    def _get_costs_dict(self, data_array, num):
        data_array = self._validate_array(data_array)
        empty_record = {'expense_id': False, 'descr': '', 'expense_total': 0, 'name': '', }
        expense_id = self.get_id_from_ext_id(COSTS_MAP[num])
        if expense_id:
            empty_record['expense_id'] = expense_id
            empty_record['descr'] = data_array[1]
            empty_record['expense_total'] = data_array[2]
        return empty_record

    def load_costs_from_xls(self):
        try:
            file_data = base64.b64decode(self.xls_file)
            book = xlrd.open_workbook(file_contents=file_data)
        except FileNotFoundError:
            raise UserError('No such file or directory found. \n%s.' % self.xls_filename)
        except xlrd.biffh.XLRDError:
            raise UserError('Only excel files are supported.')

        expenses = []
        self.expenses_ids.unlink()
        for sheet in book.sheets():
            try:
                if sheet.name in ['Marketing costs']:
                    for row in range(sheet.nrows):
                        if row >= 1:
                            row_values = sheet.row_values(row)
                            vals = self._get_costs_dict(row_values, row)
                            if not vals['expense_total']:
                                continue
                            expenses.append((0, 0, vals))
            except IndexError:
                pass
        try:
            self.expenses_ids = expenses
            if not expenses:
                self.name = _("Nothing to load")
            else:
                self.name = _("Successfully loaded")
        except ValueError:
            self.name = _("Wrong format of file")
        return {
            'name': _('Import expenses'),
            'res_model': 'ug.distrib.import.expenses',
            'view_mode': 'form',
            'res_id': self.id,
            'context': {
                'default_name': self.name,
                'default_xls_file': self.xls_file,
                'default_xls_filename': self.xls_filename,
                'default_distrib_id': self.distrib_id,
                'default_products_ids': self.expenses_ids,
                # 'active_ids': self._context.get('active_ids'),
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def _prepare_move_value(self):
        return {
            'distrib_id': self.distrib_id.id,
            'user_id': self.env.user.id,
            'date_order': self.date,
        }

    def save_expenses(self):
        so_data = self._prepare_move_value()
        Expense = self.env['distrib.marketing.expenses'].sudo()
        move_sudo = Expense.with_user(SUPERUSER_ID).create(so_data)
        move_sudo = move_sudo.with_user(self.env.user).sudo()
        expenses = []
        for line in self.expenses_ids:
            if line.expense_id:
                expense = {
                    'expense_id': line.expense_id.id,
                    'name': line.expense_id.name,
                    'expense_total': line.expense_total,
                    'descr': line.expense_id.desc,
                }
                expenses.append((0, 0, expense))
        move_sudo.move_line = expenses


class UgImportExpensesList(models.TransientModel):
    _name = "ug.distrib.import.expenses.list"
    _description = "Expenses list"
    _order = 'name'

    wizard_id = fields.Many2one('ug.distrib.import.expenses', ondelete='cascade')
    expense_id = fields.Many2one(
        comodel_name='distrib.types.marketings',
        string="Type of Expense")
    name = fields.Char('Name', readonly=True)
    descr = fields.Text('Description', required=True)
    currency_id = fields.Many2one(
        related='wizard_id.currency_id',
        store=True, precompute=True)
    expense_total = fields.Monetary(
        string="Total",
        required=True
    )
