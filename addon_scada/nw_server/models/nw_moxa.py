import psutil
import subprocess

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
            try:
                if 'MODBUS' in self.controller_id.name:
                    line.is_modbus = True
                else:
                    line.is_modbus = False
            except:
                line.is_modbus = False

    @api.model
    def get_monitor_is_running(self):
        service_name = "weight"
        for proc in psutil.process_iter():
            try:
                if proc.name() == service_name:
                    print(f"{service_name} service is running")
                    # return {
                    #     'type': 'ir.actions.client',
                    #     'tag': 'display_notification',
                    #     'params': {
                    #         'title': _('Success!'),
                    #         'message': _(f"{service_name} service is running"),
                    #         'sticky': False,
                    #     }
                    # }
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # return {
                #     'type': 'ir.actions.client',
                #     'tag': 'display_notification',
                #     'params': {
                #         'type': 'danger',
                #         'title': _('Warning!'),
                #         'message': _(f"No such process {service_name} or access denied"),
                #         'sticky': False,
                #     }
                # }
                return False
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'type': 'danger',
        #         'title': _('Warning!'),
        #         'message': _(f"{service_name} service is not running"),
        #         'sticky': False,
        #     }
        # }
        return False

    @api.model
    def restart_monitor(self):
        # Define the service name
        service_name = "weight"
        cmd = f'sudo -S systemctl restart {service_name}'

        with subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True) as process:
            # Wait for the command to complete and collect its output
            stdout, stderr = process.communicate()
            # Optionally, you can check the exit code and print the output
            if process.returncode == 0:
                print('Command succeeded:')
                print(stdout)
                return True
            else:
                print('Command failed:')
                print(stderr)
                return False

    @api.model
    def start_monitor(self):
        # Define the service name
        service_name = "weight"
        cmd = f'sudo -S systemctl start {service_name}'

        with subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True) as process:
            # Wait for the command to complete and collect its output
            stdout, stderr = process.communicate()
            # Optionally, you can check the exit code and print the output
            if process.returncode == 0:
                print('Command succeeded:')
                print(stdout)
                return True
            else:
                print('Command failed:')
                print(stderr)
                return False

    @api.model
    def stop_monitor(self):
        # Define the service name
        service_name = "weight"
        cmd = f'sudo -S systemctl stop {service_name}'

        with subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True) as process:
            # Wait for the command to complete and collect its output
            stdout, stderr = process.communicate()
            # Optionally, you can check the exit code and print the output
            if process.returncode == 0:
                print('Command succeeded:')
                print(stdout)
                return True
            else:
                print('Command failed:')
                print(stderr)
                return False
