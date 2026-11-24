from odoo import api, fields, models

LOG_EXCHANGE_PARAM = 'ug_1c_connector.log_exchange'


class ApiRestExchangeLog(models.Model):
    _name = 'api.rest.exchange.log'
    _description = '1C exchange log'
    _order = 'id desc'

    request_url = fields.Char(readonly=True)
    http_method = fields.Char(string='Method', required=True, readonly=True)
    model_name = fields.Char(string='Model', required=True, index=True, readonly=True)
    guid = fields.Char(index=True, readonly=True)
    name_preview = fields.Char(string='Name', readonly=True)
    action = fields.Selection(
        selection=[
            ('post_create', 'Created'),
            ('post_update', 'Updated'),
            ('post_empty', 'Empty body'),
            ('put_update', 'Updated by PUT'),
            ('put_skipped', 'Not found, PUT does not create'),
            ('delete', 'Deleted'),
            ('error', 'Error'),
            ('other', 'Other'),
        ],
        required=True,
        index=True,
        readonly=True,
    )
    success = fields.Boolean(readonly=True)
    res_id = fields.Integer(string='Record ID', readonly=True)
    error = fields.Text(readonly=True)
    content_type = fields.Char(readonly=True)
    body_len = fields.Integer(string='Body length', readonly=True)
    body_head = fields.Text(string='Body head', readonly=True)
    payload = fields.Text(string='Payload', readonly=True)


class ApiRestExchangeLogSetting(models.TransientModel):
    _name = 'api.rest.exchange.log.setting'
    _description = '1C exchange log setting'

    log_exchange = fields.Boolean(
        string='Write exchange log',
        help='Disable this to stop recording incoming 1C requests. '
             'Lines already stored remain in the list.',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        value = self.env['ir.config_parameter'].sudo().get_param(LOG_EXCHANGE_PARAM, 'True')
        res['log_exchange'] = str(value).strip().lower() in ('1', 'true', 'yes')
        return res

    def action_save(self):
        self.ensure_one()
        self.env['ir.config_parameter'].sudo().set_param(
            LOG_EXCHANGE_PARAM,
            'True' if self.log_exchange else 'False',
        )
        return {'type': 'ir.actions.act_window_close'}
