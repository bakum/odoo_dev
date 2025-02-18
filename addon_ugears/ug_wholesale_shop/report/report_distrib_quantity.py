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
                    DIST.ID,
                    DIST.REGION_ID
                FROM
                    DISTRIB_DISTRIBUTORS AS DIST
            ),
            QTT_REMAINS (
                ID,
                PRODUCT_ID,
                DISTRIB_ID,
                REGION_ID,
                DATE,
                CURRENCY_ID,
                CATEG_ID,
                CARTOON_ID,
                PRICE_UNIT,
                RATE,
                START_PRODUCT_QTY,
                PRODUCT_QTY,
                START_PRICE_TOTAL,
                START_PRICE_TOTAL_ACC,
                PRICE_TOTAL,
                PRICE_TOTAL_ACC,
                QTY_IN_CARTOON
            ) AS (
                SELECT
                    H.ID,
                    PRODUCT_ID,
                    DISTRIB_ID,
                    D.REGION_ID,
                    H.DATE::DATE AS REAL_DATE,
                    CURRENCY_ID,
                    PT.CATEG_ID AS CATEG_ID,
                    PT.CARTOON_ID AS CARTOON_ID,
                    PRICE_UNIT,
                    ROUND(RATE::NUMERIC, 5) AS RATE,
                    QUANTITY_BEGIN,
                    QUANTITY_END,
                    ROUND((PRICE_UNIT * QUANTITY_BEGIN)::NUMERIC, 2) AS START_PRICE_TOTAL,
                    ROUND((PRICE_UNIT * QUANTITY_BEGIN * RATE)::NUMERIC, 2) AS START_PRICE_TOTAL_ACC,
                    ROUND((PRICE_UNIT * QUANTITY_END)::NUMERIC, 2) AS PRICE_TOTAL,
                    ROUND((PRICE_UNIT * QUANTITY_END * RATE)::NUMERIC, 2) AS PRICE_TOTAL_ACC,
                    PT.QTY_IN_CARTOON AS QTY_IN_CARTOON
                FROM
                    DISTRIB_QUANT_HISTORY H
                    LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID = H.PRODUCT_ID
                    LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID = PP.PRODUCT_TMPL_ID
                    LEFT JOIN DISTRIBUTOR D ON D.ID = H.DISTRIB_ID
            )
        SELECT
            ID,
            PRODUCT_ID,
            'forecast' STATE,
            DATE,
            DISTRIB_ID,
            CATEG_ID,
            CARTOON_ID,
            QTY_IN_CARTOON,
            PRODUCT_QTY,
            CASE
                WHEN QTY_IN_CARTOON = 0 THEN 0
                ELSE ROUND(
                    (PRODUCT_QTY / QTY_IN_CARTOON)::NUMERIC,
                    2
                )
            END AS QTY_ALL_IN_CARTOON
        FROM
            QTT_REMAINS
    );
    """
        report_period = self.env['ir.config_parameter'].sudo().get_param('distrib.report_distrib_quantity_period',
                                                                         default='12')
        self.env.cr.execute(query, {'report_period': int(report_period)})


