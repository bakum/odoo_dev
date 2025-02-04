from odoo import models, fields, tools


class ReportDistribQuantity(models.Model):
    _inherit = "report.distrib.quantity"

    _depends = {
        'product.product': ['product_tmpl_id'],
        'product.template': ['type', 'cartoon_id'],
        'distrib.distributors.move.line': ['date', 'distrib_id', 'product_id', 'product_uom_qty', 'state'],
        'distrib.quant': ['distrib_id', 'product_id', 'quantity'],
    }

    cartoon_id = fields.Many2one('distrib.packages.sizes', 'Cartoon', readonly=True)
    qty_in_cartoon = fields.Integer(string='Quantity in an cartoon', readonly=True)
    qty_all_in_cartoon = fields.Float(string='Amount cartoons', readonly=True)

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
        MAIN.ID,
        MAIN.PRODUCT_ID,
        MAIN.STATE,
        MAIN.DATE,
        MAIN.DISTRIB_ID,
        PT.CATEG_ID AS CATEG_ID,
        PT.CARTOON_ID AS CARTOON_ID,
        PT.QTY_IN_CARTOON AS QTY_IN_CARTOON,
        MAIN.PRODUCT_QTY,
        CASE
            WHEN PT.QTY_IN_CARTOON = 0 THEN 0
            ELSE ROUND(
                (MAIN.PRODUCT_QTY / PT.QTY_IN_CARTOON)::NUMERIC,
                2
            )
        END AS QTY_ALL_IN_CARTOON
    FROM
        (
            SELECT
                MIN(FORECAST_QTY.ID) AS ID,
                PRODUCT_ID,
                TMPL_ID PRODUCT_TMPL_ID,
                STATE,
                DATE,
                DISTRIB_ID,
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
            GROUP BY
                PRODUCT_ID,
                TMPL_ID,
                STATE,
                DATE,
                DISTRIB_ID
        ) AS MAIN
        LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID = MAIN.PRODUCT_TMPL_ID
    );
    """
        report_period = self.env['ir.config_parameter'].sudo().get_param('distrib.report_distrib_quantity_period',
                                                                         default='12')
        self.env.cr.execute(query, {'report_period': int(report_period)})


