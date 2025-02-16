from odoo import models, fields, _
from odoo.osv import expression
from odoo.tools.misc import format_datetime


class DistribQuantityHistory(models.TransientModel):
    _name = 'distrib.quantity.history'
    _description = 'Distributor Quantity History'

    inventory_datetime = fields.Datetime('Inventory at Date',
                                         help="Choose a date to get the inventory at that date",
                                         default=fields.Datetime.now)
    distrib_id = fields.Many2one(
        'distrib.distributors', 'Distributor',
        default=lambda self: self.env.user.distrib_id.id,
        help='This is the owner of the quant')

    def open_at_date(self):
        tree_view_id = self.env.ref('ug_base_distrib.view_distrib_product_tree').id
        form_view_id = self.env.ref('product.product_template_only_form_view').id
        # domain = []
        # if self.distrib_id:
        #     domain.append(('distrib_id', '=', self.distrib_id.id))
        domain = [('type', 'in', ['consu', 'product'])]
        product_id = self.env.context.get('product_id', False)
        product_tmpl_id = self.env.context.get('product_tmpl_id', False)
        if product_id:
            domain = expression.AND([domain, [('id', '=', product_id)]])
        elif product_tmpl_id:
            domain = expression.AND([domain, [('product_tmpl_id', '=', product_tmpl_id)]])
        # We pass `to_date` in the context so that `qty_available` will be computed across
        # moves until date.
        # action = self.env['distrib.quant'].action_view_inventory()
        # # action["name"] = _('Products')
        # action['domain'] = domain
        # action['context'] = dict(self.env.context, to_date=self.inventory_datetime)
        # action['display_name']: format_datetime(self.env, self.inventory_datetime)
        self.inventory_datetime = self.inventory_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        display_name = format_datetime(self.env, self.inventory_datetime, dt_format='short') + '-'
        if self.distrib_id:
            display_name += self.distrib_id.name
        else:
            display_name += '*'
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Products'),
            'res_model': 'product.product',
            'domain': domain,
            'context': dict(self.env.context, to_date=self.inventory_datetime,
                            distrib=False if not self.distrib_id else self.distrib_id.id,
                            search_default_on_hand=1),
            'display_name': display_name
        }
        return action
