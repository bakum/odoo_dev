from odoo import models, fields, api, _


class Error(models.Model):
    _name = 'nw.error'
    _description = 'Errors records'

    moxa_id = fields.Many2one('nw.moxa', string='Moxa', required=True, translate=True)
    nid = fields.Integer('NID', required=True)
    count = fields.Integer('Count', required=True, default=0, translate=True)
    value = fields.Float('Value', required=True, translate=True)
    error = fields.Integer(string='Error', default=0, required=True, translate=True)
    message = fields.Text('Message', translate=True)
