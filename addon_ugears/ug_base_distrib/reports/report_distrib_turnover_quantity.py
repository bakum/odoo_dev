from odoo import models, fields, tools


class ReportDistribTurnoverQuantity(models.Model):
    _name = 'report.distrib.turnover.quantity'
    _auto = False
    _description = 'Distributor Turnover Quantity Report'

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
    period = fields.Selection([
        ('days', 'Days'),
        ('month', 'Months'),
        ('year', 'Years'),
    ], string='Period', readonly=True)
    start_product_qty = fields.Float(string='Beginning Stock, pcs', readonly=True)
    product_qty = fields.Float(string='Ending Stock, pcs', readonly=True)
    distrib_id = fields.Many2one('distrib.distributors', readonly=True, string='Distributor')
    categ_id = fields.Many2one('product.category', readonly=True, string='Category')
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    region_id = fields.Many2one('distrib.regions', "Region", readonly=True,
                                groups="ug_base_distrib.group_distrib_manager")
    cartoon_id = fields.Many2one('distrib.packages.sizes', 'Cartoon', readonly=True)
    start_price_total = fields.Float(string='Beginning Amount', readonly=True)
    start_price_total_acc = fields.Float(string='Beginning Amount (acc)', readonly=True,
                                         groups="ug_base_distrib.group_distrib_manager")
    price_total = fields.Float(string='Ending Amount', readonly=True)
    price_total_acc = fields.Float(string='Ending Amount (acc)', readonly=True,
                                   groups="ug_base_distrib.group_distrib_manager")
    full_name = fields.Char(string='Product Full Name', readonly=True)
    barcode = fields.Char(string='EAN', readonly=True)
    default_code = fields.Char(string='Product Code', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_distrib_turnover_quantity')
        query = """
        CREATE OR REPLACE FUNCTION public.first_agg (anyelement, anyelement)
          RETURNS anyelement
          LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE AS
        'SELECT $1';
        
        DROP AGGREGATE IF EXISTS public.first(anyelement);
        CREATE AGGREGATE public.first(anyelement) (
          SFUNC = public.first_agg
        , STYPE = anyelement
        , PARALLEL = safe
        );
        
        
        CREATE OR REPLACE FUNCTION public.last_agg (anyelement, anyelement)
          RETURNS anyelement
          LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE AS
        'SELECT $2';
        
        DROP AGGREGATE IF EXISTS public.last(anyelement);
        CREATE AGGREGATE public.last(anyelement) (
          SFUNC = public.last_agg
        , STYPE = anyelement
        , PARALLEL = safe
        );
        CREATE or REPLACE VIEW report_distrib_turnover_quantity AS (
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
                PRICE_TOTAL_ACC
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
                    ROUND((PRICE_UNIT * QUANTITY_END * RATE)::NUMERIC, 2) AS PRICE_TOTAL_ACC
                FROM
                    DISTRIB_QUANT_HISTORY H
                    LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID = H.PRODUCT_ID
                    LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID = PP.PRODUCT_TMPL_ID
                    LEFT JOIN DISTRIBUTOR D ON D.ID = H.DISTRIB_ID
            ),
            LAST_IDS AS (
                SELECT
                    FIRST (ID) AS ID,
                    DISTRIB_ID,
                    PRODUCT_ID
                FROM
                    (
                        SELECT
                            ID,
                            DISTRIB_ID,
                            PRODUCT_ID
                        FROM
                            QTT_REMAINS
                        ORDER BY
                            DISTRIB_ID,
                            PRODUCT_ID,
                            DATE DESC
                    ) AS MAIN
                GROUP BY
                    DISTRIB_ID,
                    PRODUCT_ID
            ),
            CURRENT_VALUES (
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
                PRICE_TOTAL_ACC
            ) AS (
                SELECT
                    ID,
                    PRODUCT_ID,
                    DISTRIB_ID,
                    REGION_ID,
                    GEN_DATE,
                    CURRENCY_ID,
                    CATEG_ID,
                    CARTOON_ID,
                    PRICE_UNIT,
                    RATE,
                    CASE
                        WHEN DATE <> GEN_DATE THEN PRODUCT_QTY
                        ELSE START_PRODUCT_QTY
                    END AS START_PRODUCT_QTY,
                    PRODUCT_QTY,
                    CASE
                        WHEN DATE <> GEN_DATE THEN PRICE_TOTAL
                        ELSE START_PRICE_TOTAL
                    END AS START_PRICE_TOTAL,
                    CASE
                        WHEN DATE <> GEN_DATE THEN PRICE_TOTAL_ACC
                        ELSE START_PRICE_TOTAL_ACC
                    END AS START_PRICE_TOTAL_ACC,
                    PRICE_TOTAL,
                    PRICE_TOTAL_ACC
                FROM
                    (
                        SELECT
                            ID,
                            PRODUCT_ID,
                            DISTRIB_ID,
                            REGION_ID,
                            GENERATE_SERIES(
                                DATE::DATE,
                                (NOW() AT TIME ZONE 'utc')::DATE + INTERVAL '1 day',
                                '1 day'::INTERVAL
                            )::DATE GEN_DATE,
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
                            PRICE_TOTAL_ACC
                        FROM
                            QTT_REMAINS
                        WHERE
                            ID IN (
                                SELECT
                                    IDS.ID
                                FROM
                                    LAST_IDS IDS
                            )
                    ) AS MAIN
            ),
            ALL_DM_DAYS AS (
                SELECT DISTINCT
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
                    PRICE_TOTAL_ACC
                FROM
                    (
                        SELECT
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
                            PRICE_TOTAL_ACC
                        FROM
                            QTT_REMAINS
                        UNION ALL
                        SELECT
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
                            PRICE_TOTAL_ACC
                        FROM
                            CURRENT_VALUES
                    ) AS MAIN
            ),
            ALL_DM_MONTHS AS (
                SELECT
                    MIN(ID) AS ID,
                    PRODUCT_ID,
                    DISTRIB_ID,
                    REGION_ID,
                    DATE_TRUNC('MONTH', DATE)::DATE AS DATE,
                    'month' AS PERIOD,
                    'forecast' AS STATE,
                    CURRENCY_ID,
                    CATEG_ID,
                    CARTOON_ID,
                    AVG(PRICE_UNIT) AS PRICE_UNIT,
                    AVG(RATE) AS RATE,
                    FIRST (START_PRODUCT_QTY) AS START_PRODUCT_QTY,
                    LAST (PRODUCT_QTY) AS PRODUCT_QTY,
                    FIRST (START_PRICE_TOTAL) AS START_PRICE_TOTAL,
                    FIRST (START_PRICE_TOTAL_ACC) AS START_PRICE_TOTAL_ACC,
                    LAST (PRICE_TOTAL) AS PRICE_TOTAL,
                    LAST (PRICE_TOTAL_ACC) AS PRICE_TOTAL_ACC
                FROM
                    (
                        SELECT
                            *
                        FROM
                            ALL_DM_DAYS
                        ORDER BY
                            DISTRIB_ID,
                            PRODUCT_ID,
                            DATE
                    ) AS MAIN
                GROUP BY
                    PRODUCT_ID,
                    DISTRIB_ID,
                    REGION_ID,
                    DATE_TRUNC('MONTH', DATE)::DATE,
                    CURRENCY_ID,
                    CATEG_ID,
                    CARTOON_ID
            ),
            ALL_DM_YEARS AS (
                SELECT
                    MIN(ID) AS ID,
                    PRODUCT_ID,
                    DISTRIB_ID,
                    REGION_ID,
                    DATE_TRUNC('YEAR', DATE)::DATE AS DATE,
                    'year' AS PERIOD,
                    'forecast' AS STATE,
                    CURRENCY_ID,
                    CATEG_ID,
                    CARTOON_ID,
                    AVG(PRICE_UNIT) AS PRICE_UNIT,
                    AVG(RATE) AS RATE,
                    FIRST (START_PRODUCT_QTY) AS START_PRODUCT_QTY,
                    LAST (PRODUCT_QTY) AS PRODUCT_QTY,
                    FIRST (START_PRICE_TOTAL) AS START_PRICE_TOTAL,
                    FIRST (START_PRICE_TOTAL_ACC) AS START_PRICE_TOTAL_ACC,
                    LAST (PRICE_TOTAL) AS PRICE_TOTAL,
                    LAST (PRICE_TOTAL_ACC) AS PRICE_TOTAL_ACC
                FROM
                    (
                        SELECT
                            *
                        FROM
                            ALL_DM_DAYS
                        ORDER BY
                            DISTRIB_ID,
                            PRODUCT_ID,
                            DATE
                    ) AS MAIN
                GROUP BY
                    PRODUCT_ID,
                    DISTRIB_ID,
                    REGION_ID,
                    DATE_TRUNC('YEAR', DATE)::DATE,
                    CURRENCY_ID,
                    CATEG_ID,
                    CARTOON_ID
            )
        SELECT
            MAIN.ID,
            PRODUCT_ID,
            PP.BARCODE,
            PP.DEFAULT_CODE,
            CONCAT(
                PT.NAME -> 'en_US',
                '/',
                PP.BARCODE,
                '/',
                PP.DEFAULT_CODE
            ) AS FULL_NAME,
            STATE,
            PERIOD,
            DATE,
            DISTRIB_ID,
            REGION_ID,
            MAIN.CATEG_ID,
            MAIN.CARTOON_ID,
            MAIN.CURRENCY_ID,
            START_PRODUCT_QTY,
            PRODUCT_QTY,
            START_PRICE_TOTAL,
            START_PRICE_TOTAL_ACC,
            PRICE_TOTAL,
            PRICE_TOTAL_ACC
        FROM
            (
                SELECT
                    ID,
                    PRODUCT_ID,
                    STATE,
                    PERIOD,
                    DATE,
                    DISTRIB_ID,
                    REGION_ID,
                    CATEG_ID,
                    CARTOON_ID,
                    CURRENCY_ID,
                    START_PRODUCT_QTY,
                    PRODUCT_QTY,
                    START_PRICE_TOTAL,
                    START_PRICE_TOTAL_ACC,
                    PRICE_TOTAL,
                    PRICE_TOTAL_ACC
                FROM
                    ALL_DM_MONTHS AS MM
                UNION ALL
                SELECT
                    ID,
                    PRODUCT_ID,
                    'forecast' AS STATE,
                    'days' AS PERIOD,
                    DATE,
                    DISTRIB_ID,
                    REGION_ID,
                    CATEG_ID,
                    CARTOON_ID,
                    CURRENCY_ID,
                    START_PRODUCT_QTY,
                    PRODUCT_QTY,
                    START_PRICE_TOTAL,
                    START_PRICE_TOTAL_ACC,
                    PRICE_TOTAL,
                    PRICE_TOTAL_ACC
                FROM
                    ALL_DM_DAYS AS MM
                UNION ALL
                SELECT
                    ID,
                    PRODUCT_ID,
                    STATE,
                    PERIOD,
                    DATE,
                    DISTRIB_ID,
                    REGION_ID,
                    CATEG_ID,
                    CARTOON_ID,
                    CURRENCY_ID,
                    START_PRODUCT_QTY,
                    PRODUCT_QTY,
                    START_PRICE_TOTAL,
                    START_PRICE_TOTAL_ACC,
                    PRICE_TOTAL,
                    PRICE_TOTAL_ACC
                FROM
                    ALL_DM_YEARS AS MM
            ) AS MAIN
            LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID = MAIN.PRODUCT_ID
            LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID = PP.PRODUCT_TMPL_ID
    );
    """
        report_period = self.env['ir.config_parameter'].sudo().get_param('distrib.report_distrib_quantity_period',
                                                                         default='12')
        self.env.cr.execute(query, {'report_period': int(report_period)})
