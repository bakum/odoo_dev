from odoo import models, fields, api, _


class Weight(models.Model):
    _name = 'nw.weight'
    _description = 'Weight records'

    moxa_id = fields.Many2one('nw.moxa', string='Moxa', required=True)
    nid = fields.Char('NID', required=True)
    count = fields.Integer('Count', required=True, default=0)
    value1 = fields.Float('Value1', required=True)
    value2 = fields.Float('Value2', required=True, default=0)
    error = fields.Integer(string='Error', default=0, required=True)
    message = fields.Text(string='Message')

    def compute_current_weight(self, moxa_id=0):
        sql = """SELECT moxa_id, nm.name,
                        nm.ip,
                         nm.port,
                         nm.module,
                         lval1 AS value1,
                         lval2 AS value2,
                         lcount AS count,
                         lnid AS nid,
                         lerror AS error,
                         lmessage AS message
                  FROM                  (
                          SELECT DISTINCT moxa_id,
                                          LAST_VALUE(COUNT) OVER (PARTITION BY moxa_id
                                              ORDER BY write_date RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS lcount,
                                          LAST_VALUE(VALUE1) OVER (PARTITION BY moxa_id
                                              ORDER BY write_date RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS lVal1,
                                          LAST_VALUE(VALUE2) OVER (PARTITION BY moxa_id
                                              ORDER BY write_date RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS lVal2,
                                          LAST_VALUE(nid) OVER (PARTITION BY moxa_id
                                              ORDER BY write_date RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS lnid,
                                          LAST_VALUE(error) OVER (PARTITION BY moxa_id
                                              ORDER BY write_date RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS lerror,
                                          LAST_VALUE(message) OVER (PARTITION BY moxa_id
                                              ORDER BY write_date RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS lmessage
                          FROM nw_weight) AS weight
                          LEFT JOIN nw_moxa nm ON nm.id = weight.moxa_id
                  WHERE nm.active = true and moxa_id = %s
                  """
        self.env.cr.execute(sql, [moxa_id])
        curr_weight = self.env.cr.dictfetchall()
        # print(moxa_id)
        if len(curr_weight) == 0:
            return {}
        return curr_weight[0]

    def _truncate_old_records_by_moxa(self, moxa_id):
        day_count = self.env['ir.config_parameter'].sudo().get_param('nw_server.default_last_dey_count')
        if int(day_count) <= 0:
            return
        sql = """
            select * from (select *, row_number() OVER () as rnum
                from
                (select max(id) id, date(write_date) write_date from nw_weight
                    where moxa_id = %s
                group by  date(write_date)
                order by write_date desc) as main) as supermain
            where supermain.rnum > %s
            limit 1
        """
        self.env.cr.execute(sql, [moxa_id, day_count])
        curr_ids = self.env.cr.dictfetchall()
        if len(curr_ids) == 0:
            return
        id = curr_ids[0]['id']
        line_to_delete = self.env['nw.weight'].sudo().search(['&', ('id', '<', id), ('moxa_id.id', '=', moxa_id)])
        for line in line_to_delete:
            line.unlink()

    def _truncate_old_records(self):
        moxa_line = self.env['nw.moxa'].sudo().search_read([('active', '=', True)])
        for moxa in moxa_line:
            self._truncate_old_records_by_moxa(moxa['id'])
