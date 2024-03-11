from odoo import models, fields, api, _


class Error(models.Model):
    _name = 'nw.error'
    _description = 'Errors records'

    moxa_id = fields.Many2one('nw.moxa', string='Moxa', required=True)
    nid = fields.Char('NID', required=True)
    count = fields.Integer('Count', required=True, default=0)
    value = fields.Float('Value', required=True)
    error = fields.Integer(string='Error', default=0, required=True)
    message = fields.Text('Message')
