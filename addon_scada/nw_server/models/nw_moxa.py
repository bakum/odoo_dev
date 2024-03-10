from odoo import models, fields, api, _


class Moxa(models.Model):
    _name = 'nw.moxa'
    _description = 'Moxa records'

    controller_id = fields.Many2one('nw.types.controllers', string='Controller', required=True)
    name = fields.Char(string='Name', required=True)
    ip = fields.Char(string='IP', required=True, default=lambda self: _("127.0.0.1"))
    com = fields.Char(string='COM', required=True, default=lambda self: _("COM1"))
    port = fields.Integer(string='Port', required=True, default=lambda self: 0)
    module = fields.Char(string='Module', required=True)
    connection_timeout = fields.Integer(string='Connection Timeout', default=lambda self: 2)
    repeat_timeout = fields.Integer(string='Repeat Timeout', default=lambda self: 5)
    error_timeout = fields.Integer(string='ErrorTimeout', default=lambda self: 5)

    is_modbus = fields.Boolean(string='Is Modbus', default=False)
    start_register = fields.Integer(string='Start address', required=True, default=lambda self: 0)
    register_offset = fields.Integer(string='Count registers', required=True, default=lambda self: 0)
    hight_byte_first = fields.Boolean(string='Hight byte first', default=True)
    hight_word_first = fields.Boolean(string='Hight word first', default=False)
    hight_dword_first = fields.Boolean(string='Hight double word first', default=False)
    slave_id = fields.Integer(string='Slave ID', required=True, default=lambda self: 0)
    multiplexer = fields.Float(string='Result multiplexer', digits=(5, 6), default=lambda self: 1.0)
    modbus_type_value = fields.Selection(
        selection=[
            ('MCT_BYTE', "MCT_BYTE"),
            ('MCT_WORD', "MCT_WORD"),
            ('MCT_DWORD', "MCT_DWORD"),
            ('MCT_DOUBLE', "MCT_DOUBLE"),
            ('MCT_INT', "MCT_INT"),
            ('MCT_INT64', "MCT_INT64"),
            ('MCT_UINT64', "MCT_UINT64"),
            ('MCT_BIT', "MCT_BIT"),
            ('MCT_INT16', "MCT_INT16"),
        ],
        string="Register type of value", required=True,
        copy=False, index=True,
        default='MCT_WORD')
    baud_rate = fields.Selection(
        selection=[
            ('9600', "9600"),
            ('19200', "19200"),
            ('28800', "28800"),
            ('57600', "57600"),
            ('115200', "115200"),
        ],
        string="Baud Rate", required=True,
        copy=False, index=True,
        default='9600')
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
            if 'MODBUS' in self.controller_id.name:
                line.is_modbus = True