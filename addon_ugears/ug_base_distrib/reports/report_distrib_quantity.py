from odoo import models, fields, tools


class ReportDistribQuantity(models.Model):
    _name = 'report.distrib.quantity'
    _auto = False
    _description = 'Distributor Quantity Report'

    _depends = {
        'product.product': ['product_tmpl_id'],
        'product.template': ['type'],
        'distrib.distributors.move.line': ['date', 'distrib_id', 'product_id', 'product_uom_qty', 'state'],
        'distrib.quant': ['distrib_id', 'product_id', 'quantity'],
    }

    date = fields.Date(string='Date', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    state = fields.Selection([
        ('forecast', 'Forecasted Stock'),
        ('in', 'Forecasted Receipts'),
        ('out', 'Forecasted Deliveries'),
    ], string='State', readonly=True)
    product_qty = fields.Float(string='Quantity', readonly=True)
    distrib_id = fields.Many2one('distrib.distributors', readonly=True, string='Distributor')
    categ_id = fields.Many2one('product.category', readonly=True, string='Category')

    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_distrib_quantity')
        query = """
        CREATE or REPLACE VIEW report_distrib_quantity AS (
        WITH
            DISTRIBUTOR AS (
                SELECT
                    DIST.ID
                FROM
                    DISTRIB_DISTRIBUTORS AS DIST
            ),
            EXISTING_DM (
                ID,
                DISTRIB_ID,
                PRODUCT_ID,
                TMPL_ID,
                PRODUCT_QTY,
                DATE,
                STATE
            ) AS (
                SELECT
                    DM.ID,
                    DM.DISTRIB_ID,
                    DM.PRODUCT_ID,
                    PT.ID,
                    DM.BALANCE,
                    DM.DATE,
                    DM.STATE
                FROM
                    DISTRIB_DISTRIBUTORS_MOVE_LINE DM
                    LEFT JOIN DISTRIBUTOR SOURCE ON SOURCE.ID = DM.DISTRIB_ID
                    LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID = DM.PRODUCT_ID
                    LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID = PP.PRODUCT_TMPL_ID
                WHERE
                    PT.TYPE = 'consu'
                    AND DM.PRODUCT_UOM_QTY != 0
                    AND DM.STATE NOT IN ('draft', 'cancel')
            ),
            QUANTS (
                ID,
                DISTRIB_ID,
                PRODUCT_ID,
                TMPL_ID,
                PRODUCT_QTY,
                DATE,
                STATE
            ) AS (
                SELECT
                    Q.ID,
                    Q.DISTRIB_ID,
                    Q.PRODUCT_ID,
                    PP.PRODUCT_TMPL_ID,
                    Q.QUANTITY,
                    DATE.*::DATE,
                    'forecast' AS STATE
                FROM
                    GENERATE_SERIES(
                        (NOW() AT TIME ZONE 'utc')::DATE - INTERVAL '%(report_period)s month',
                        (NOW() AT TIME ZONE 'utc')::DATE + INTERVAL '%(report_period)s month',
                        '1 day'::INTERVAL
                    ) DATE,
                    DISTRIB_QUANT Q
                    LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID = Q.PRODUCT_ID
            ),
            ALL_DM (
                ID,
                DISTRIB_ID,
                PRODUCT_ID,
                TMPL_ID,
                PRODUCT_QTY,
                DATE,
                REAL_DATE,
                STATE
            ) AS (
                SELECT
                    ID,
                    DISTRIB_ID,
                    PRODUCT_ID,
                    TMPL_ID,
                    PRODUCT_QTY,
                    GENERATE_SERIES(
                        (NOW() AT TIME ZONE 'utc')::DATE - INTERVAL '%(report_period)s month',
                        M.DATE::DATE + INTERVAL '%(report_period)s month',
                        '1 day'::INTERVAL
                    )::DATE DATE,
                    M.DATE::DATE AS REAL_DATE,
                    'forecast' AS STATE
                FROM
                    EXISTING_DM AS M
            )
        SELECT
            MIN(FORECAST_QTY.ID) AS ID,
            PRODUCT_ID,
            TMPL_ID PRODUCT_TMPL_ID,
            STATE,
            DATE,
            DISTRIB_ID,
            PT.CATEG_ID,
            SUM(PRODUCT_QTY) AS PRODUCT_QTY
        FROM
            (
                SELECT
                    M.ID,
                    M.PRODUCT_ID,
                    M.TMPL_ID,
                    CASE
                        WHEN M.PRODUCT_QTY < 0 THEN 'out'
                        WHEN M.PRODUCT_QTY > 0 THEN 'in'
                    END AS STATE,
                    M.DATE::DATE AS DATE,
                    DISTRIB_ID,
                    PRODUCT_QTY
                FROM
                    EXISTING_DM M
                UNION ALL
                SELECT
                    ID,
                    PRODUCT_ID,
                    TMPL_ID,
                    STATE,
                    DATE,
                    DISTRIB_ID,
                    PRODUCT_QTY
                FROM
                    QUANTS
                UNION ALL
                SELECT
                    ID,
                    PRODUCT_ID,
                    TMPL_ID,
                    STATE,
                    DATE,
                    DISTRIB_ID,
                    CASE
                        WHEN REAL_DATE > DATE THEN - PRODUCT_QTY
                        ELSE 0
                    END AS PRODUCT_QTY
                FROM
                    ALL_DM
            ) AS FORECAST_QTY
            LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID = FORECAST_QTY.TMPL_ID
            LEFT JOIN PRODUCT_CATEGORY PC ON PC.ID = PT.CATEG_ID
        GROUP BY
            PRODUCT_ID,
            TMPL_ID,
            STATE,
            DATE,
            DISTRIB_ID,
            PT.CATEG_ID
    );
    """
        report_period = self.env['ir.config_parameter'].sudo().get_param('distrib.report_distrib_quantity_period',
                                                                         default='3')
        self.env.cr.execute(query, {'report_period': int(report_period)})
