from odoo import models, fields, api


class MarketingExpensesLines(models.Model):
    _name = 'distrib.marketing.expenses.line'
    _description = 'Msrketing Expenses Lines'
    _rec_names_search = ['name', 'move_id.name']
    _order = 'move_id, distrib_id asc, id'

    _sql_constraints = [
        ('expenses_total__check', 'CHECK(expense_total>0)', 'Expenses amount cannot be zero')
    ]

    move_id = fields.Many2one(
        comodel_name='distrib.marketing.expenses',
        string="Expenses Move Reference",
        required=True, ondelete='cascade', index=True, copy=False)
    distrib_id = fields.Many2one(
        related='move_id.distrib_id',
        store=True, index=True, precompute=True)
    currency_id = fields.Many2one(
        related='move_id.distrib_id.pricelist_id.currency_id',
        store=True, index=True, precompute=True)
    date = fields.Datetime(related='move_id.date_order', string="Expenses Data", store=True, precompute=True)
    year = fields.Char(related='move_id.year', string="Expenses Year", store=True, precompute=True)
    month = fields.Selection(related='move_id.month', string="Expenses Month", store=True, precompute=True)
    salesman_id = fields.Many2one(
        related='move_id.user_id',
        string="User",
        store=True, precompute=True)
    state = fields.Selection(
        related='move_id.state',
        string="Move Status",
        copy=False, store=True, precompute=True)
    name = fields.Text(
        string="Label",
        compute='_compute_name',
        store=True, readonly=False, required=True, precompute=True)
    expense_id = fields.Many2one(
        comodel_name='distrib.types.marketings',
        string="Type of Expense",
        change_default=True, ondelete='restrict', index='btree_not_null',
        required=True,
        domain="[('active', '=', True)]")
    expense_total = fields.Monetary(
        string="Total",
        required=True
    )
    display_type = fields.Selection(
        selection=[
            ('expense', 'Expense'),
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False)

    @api.depends('expense_id')
    def _compute_name(self):
        for line in self:
            if not line.expense_id:
                continue
            name = line.expense_id.get_expenses_multiline_description()
            line.name = name
