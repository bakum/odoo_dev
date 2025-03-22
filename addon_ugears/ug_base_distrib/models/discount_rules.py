from odoo import fields, models, _, api
from odoo.exceptions import ValidationError


class DiscountRules(models.Model):
    _name = 'distrib.discount.rules'
    _description = 'Distributors generic discounts rules'

    name = fields.Char('Ref', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))

    move_line = fields.One2many(
        comodel_name='distrib.discount.rules.line',
        inverse_name='move_id',
        string="Rule Lines",
        copy=True)

    main_req = fields.Integer("Main Rule", required=True, default=1)
    active = fields.Boolean(default=True)

    @api.constrains('main_req')
    def _check_main_req(self):
        for rec in self:
            domain = ['|', ('active','=',True),  ('active','=',False)]
            count = self.sudo().search_count(domain)
            if count > 1:
                raise ValidationError(_("Distributors generic discounts rules should be unique"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = 'Default Discount Rule'
        return super(DiscountRules, self).create(vals_list)

    def unlink(self):
        return super(DiscountRules, self).unlink()


    def _excluded_position(self, product_rec):
        current = self.sudo().search([])[:1]
        if current:
            rules = current.move_line
            domain = ['|',('product_id', '=', product_rec.product_id.id),('categ_id', '=', product_rec.product_id.product_tmpl_id.categ_id.id)]
            count = rules.sudo().search_count(domain)
            return count > 0
        return False


class DiscountRulesLines(models.Model):
    _name = 'distrib.discount.rules.line'
    _description = 'Distributors generic discounts rules lines'

    move_id = fields.Many2one(
        comodel_name='distrib.discount.rules',
        string="Discount Rule Reference",
        required=True, ondelete='cascade', index=True, copy=False)

    categ_id = fields.Many2one(
        'product.category', 'Product Category',
        change_default=True)

    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product",
        change_default=True, ondelete='restrict', index='btree_not_null',
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

    @api.depends('product_id')
    def _compute_product_template_id(self):
        for line in self:
            line.product_template_id = line.product_id.product_tmpl_id

    def _search_product_template_id(self, operator, value):
        return [('product_id.product_tmpl_id', operator, value)]
