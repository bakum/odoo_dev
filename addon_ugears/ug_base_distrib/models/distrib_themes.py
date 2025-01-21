from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductThemes(models.Model):
    _name = 'distrib.product.theme'
    _description = 'Product theme'

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(default=True)
    guid = fields.Char(string='Guid 1C:Enterprise')
    product_ids = fields.One2many(
        comodel_name='product.template',
        inverse_name='theme_id',
        string="Theming Products")

    @api.ondelete(at_uninstall=False)
    def _unlink_except_used_as_rule_base(self):
        linked_items = self.env['product.template'].sudo().with_context(active_test=False).search([
            ('theme_id', 'in', self.ids),
        ])
        if linked_items:
            raise UserError(_(
                'You cannot delete those theme(s):\n(%s)\n, they are used in other product(s):\n%s',
                '\n'.join(linked_items.theme_id.mapped('display_name')),
                '\n'.join(linked_items.mapped('display_name'))
            ))

    def unlink(self):
        return super(ProductThemes, self).unlink()
