from odoo import fields, models, api, _


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

    def load_budget_from_xls(self):
        pass

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
