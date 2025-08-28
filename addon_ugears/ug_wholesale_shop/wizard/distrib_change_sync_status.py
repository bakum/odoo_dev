from odoo import models, fields


class DistribChangeSyncStatus(models.TransientModel):
    _name = "distrib.change.sync.status"
    _description = "Change Status for syncronization"

    order_id = fields.Many2one('sale.order', 'Order', required=True)
    sync_state = fields.Selection(
        selection=[
            ('new', "New"),
            ('deployment', "Ready for syncronization"),
            ('error', "Error on syncronization"),
            ('done', "Syncronized"),
        ],
        string="Syncronization Status", required=True,)

    def save_status(self):
        self.order_id.write({'sync_state': self.sync_state, 'sync_note': False})    