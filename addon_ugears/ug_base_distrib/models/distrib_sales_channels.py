from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductChannels(models.Model):
    _name = 'distrib.sales.channels'
    _description = 'Sales Channels'

    name = fields.Char(string='Name', required=True)
    report_description = fields.Char(string='Description')
    active = fields.Boolean(default=True)
    guid = fields.Char(string='Guid 1C:Enterprise')

    @api.ondelete(at_uninstall=False)
    def _unlink_except_used_as_rule_base(self):
        linked_items = self.env['distrib.distributors.move.line'].sudo().with_context(active_test=False).search(['|',
            ('channel_id', 'in', self.ids),
            ('move_id.channel_id', 'in', self.ids),
        ])
        if linked_items:
            raise UserError(_(
                'You cannot delete those channel(s):\n(%s)\n, they are used in other distributor''s move(s):\n%s',
                '\n'.join(linked_items.channel_id.mapped('display_name')),
                '\n'.join(linked_items.move_id.mapped('display_name'))
            ))

    def unlink(self):
        return super(ProductChannels, self).unlink()
