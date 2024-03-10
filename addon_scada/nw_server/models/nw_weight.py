from odoo import models, fields, api, _


class Weight(models.Model):
    _name = 'nw.weight'
    _description = 'Weight records'

    moxa_id = fields.Many2one('nw.moxa', string='Moxa', required=True)
    nid = fields.Integer('NID', required=True)
    count = fields.Integer('Count', required=True, default=0)
    value1 = fields.Float('Value1', required=True)
    value2 = fields.Float('Value2', required=True, default=0)
    error = fields.Integer(string='Error', default=0, required=True)
    message = fields.Text('Message', translate=True)
