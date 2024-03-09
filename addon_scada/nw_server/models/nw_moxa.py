from odoo import models, fields, api, _


class Moxa(models.Model):
    _name = 'nw.moxa'
    _description = 'Moxa records'

    controller_id = fields.Many2one('nw.types.controllers', string='Controller', required=True)
    name = fields.Char(string='Name', required=True)
    ip = fields.Char(string='IP', required=True, default=lambda self: _("127.0.0.1"))
    port = fields.Integer(string='Port', required=True, default=lambda self: 0)
    module = fields.Char(string='Module', required=True)
    connection_timeout = fields.Float(string='Connection Timeout', default=lambda self: 2.0)
    repeat_timeout = fields.Float(string='Repeat Timeout', default=lambda self: 1.0)
    error_timeout = fields.Float(string='ErrorTimeout', default=lambda self: 5.0)
    serial_type = fields.Selection(
        selection=[
            ('com', "COM"),
            ('tcp', "TCP/IP"),
        ],
        string="Connection type",
        copy=False, index=True,
        default='tcp')
    active = fields.Boolean(string='Active', default=True)
    desc = fields.Text(string='Description')

    weight_line = fields.One2many(comodel_name='nw.weight',
                                  inverse_name='moxa_id', string='Posted weight')

    @api.onchange('controller_id')
    def _onchange_controller_id(self):
        for line in self:
            line.module = self.controller_id.name
