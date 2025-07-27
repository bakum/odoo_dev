from odoo import models, fields, tools


class ReportDistribSales(models.Model):
    _name = 'report.distrib.sales'
    _auto = False
    _description = 'Distributor Sales Report'

    _depends = {
        'product.product': ['product_tmpl_id'],
        'product.template': ['type'],
        'distrib.distributors.move.line': ['date', 'distrib_id', 'product_id', 'product_uom_qty', 'state'],
    }

    date = fields.Date(string='Date', readonly=True)
    distrib_id = fields.Many2one('distrib.distributors', readonly=True, string='Distributor')
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    channel_id = fields.Many2one('distrib.sales.channels', string='Channel', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', readonly=True, groups="ug_base_distrib.group_distrib_manager")
    product_category_id = fields.Many2one('product.category', readonly=True, string='Category')
    beginning_stock = fields.Float(string='Beginning stock, pcs', readonly=True, group_operator='sum')
    sell_in = fields.Float(string='UGmodels Sell-In. pcs', readonly=True, group_operator='sum')
    sell_in_curr = fields.Float(string='UGmodels Sell-In', readonly=True, group_operator='sum')
    sell_in_acc = fields.Float(string='UGmodels Sell-In, (acc)', readonly=True, group_operator='sum',
                               groups="ug_base_distrib.group_distrib_manager")

    balance = fields.Float(string='pcs', readonly=True)
    price_total = fields.Float(string='Amount', readonly=True)
    price_total_acc = fields.Float(string='Amount (acc)', readonly=True,
                                   groups="ug_base_distrib.group_distrib_manager")
    full_name = fields.Char(string='Product Full Name', readonly=True)
    barcode = fields.Char(string='EAN', readonly=True)
    default_code = fields.Char(related='product_id.default_code', depends=['product_id'])
    # barcode = fields.Char(related='product_id.barcode',
    #                       depends=['product_id'],
    #                       help="International Article Number used for product identification.")

    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_distrib_sales')
        query = """
        CREATE or REPLACE VIEW report_distrib_sales AS (
           WITH
        -- Пронумерованные каналы
        CHANNELS (ID, ROW_NUM) AS (
            SELECT
                DSC.ID,
                ROW_NUMBER() OVER (
                    ORDER BY
                        DSC.ID
                ) AS ROW_NUM
            FROM
                DISTRIB_SALES_CHANNELS DSC
        ),
        -- Основной набор данных
        MOVE_OUT AS MATERIALIZED (
            SELECT
                CASE
                    WHEN C.ROW_NUM = 1 THEN DML.ID
                    ELSE C.ROW_NUM
                END AS ID,
                DISTRIB_ID,
                CURRENCY_ID,
                C.ID AS CHANNEL_ID,
                PRODUCT_ID,
                PP.PRODUCT_TMPL_ID,
                DML.BARCODE,
                DML.DEFAULT_CODE,
                FULL_NAME,
                PRODUCT_CATEGORY_ID,
                STATE,
                CASE
                    WHEN C.ROW_NUM = 1 THEN BEGINNING_STOCK
                    ELSE NULL
                END AS BEGINNING_STOCK,
                CASE
                    WHEN C.ROW_NUM = 1
                    AND OPERATION = 'inc' THEN BALANCE
                    WHEN C.ROW_NUM = 1
                    AND OPERATION = 'out' THEN 0
                    ELSE NULL
                END AS SELL_IN,
                CASE
                    WHEN C.ROW_NUM = 1
                    AND OPERATION = 'inc' THEN PRICE_TOTAL
                    WHEN C.ROW_NUM = 1
                    AND OPERATION = 'out' THEN 0
                    ELSE NULL
                END AS SELL_IN_CURR,
                CASE
                    WHEN C.ROW_NUM = 1
                    AND OPERATION = 'inc' THEN PRICE_TOTAL * RATE
                    WHEN C.ROW_NUM = 1
                    AND OPERATION = 'out' THEN 0
                    ELSE NULL
                END AS SELL_IN_ACC,
                OPERATION,
                CASE
                    WHEN C.ID = DML.CHANNEL_ID
                    AND OPERATION = 'out' THEN PRICE_TOTAL
                    WHEN OPERATION = 'inc' THEN 0
                    ELSE NULL
                END AS PRICE_TOTAL,
                DATE_TRUNC('MONTH', DATE)::DATE AS DATE,
                CASE
                    WHEN C.ID = DML.CHANNEL_ID
                    AND OPERATION = 'out' THEN BALANCE
                    WHEN OPERATION = 'inc' THEN 0
                    ELSE NULL
                END AS BALANCE,
                CASE
                    WHEN C.ID = DML.CHANNEL_ID
                    AND OPERATION = 'out' THEN PRICE_TOTAL * RATE
                    WHEN OPERATION = 'inc' THEN 0
                    ELSE NULL
                END AS PRICE_TOTAL_ACC
            FROM
                DISTRIB_DISTRIBUTORS_MOVE_LINE DML
                LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID = DML.PRODUCT_ID,
                CHANNELS C
            WHERE
                STATE IN ('done')
                AND OPERATION IN ('out', 'inc')
                AND NOT IS_INVENTORY
                AND DML.DISPLAY_TYPE = 'product'
        ),
        -- Только по одной строке с BEGINNING_STOCK на группу
        BEGINNING_STOCKS AS (
            SELECT
                ID,
                DISTRIB_ID,
                PRODUCT_ID,
                DATE,
                BEGINNING_STOCK
            FROM
                (
                    SELECT
                        *,
                        ROW_NUMBER() OVER (
                            PARTITION BY
                                DISTRIB_ID,
                                PRODUCT_ID,
                                DATE
                            ORDER BY
                                ID
                        ) AS RN
                    FROM
                        MOVE_OUT
                    WHERE
                        BEGINNING_STOCK IS NOT NULL
                ) T
            WHERE
                RN = 1
        ),
        -- Финальная агрегация
        MOVE_OUT_AGG AS (
            SELECT
                M.ID,
                M.DATE,
                M.DISTRIB_ID,
                M.CURRENCY_ID,
                M.CHANNEL_ID,
                M.PRODUCT_ID,
                M.PRODUCT_TMPL_ID,
                M.BARCODE,
                M.DEFAULT_CODE,
                M.FULL_NAME,
                M.PRODUCT_CATEGORY_ID,
                M.SELL_IN,
                M.SELL_IN_CURR,
                M.SELL_IN_ACC,
                M.PRICE_TOTAL,
                - M.BALANCE AS BALANCE,
                M.PRICE_TOTAL_ACC,
                BS.BEGINNING_STOCK
            FROM
                MOVE_OUT M
                LEFT JOIN BEGINNING_STOCKS BS ON BS.DISTRIB_ID = M.DISTRIB_ID
                AND BS.PRODUCT_ID = M.PRODUCT_ID
                AND BS.DATE = M.DATE
                AND BS.ID = M.ID
        )
        -- Вывод
    SELECT
        ID,
        DATE,
        DISTRIB_ID,
        CURRENCY_ID,
        CHANNEL_ID,
        PRODUCT_ID,
        PRODUCT_TMPL_ID,
        BARCODE,
        DEFAULT_CODE,
        FULL_NAME,
        PRODUCT_CATEGORY_ID,
        SELL_IN,
        SELL_IN_CURR,
        SELL_IN_ACC,
        PRICE_TOTAL,
        BALANCE,
        PRICE_TOTAL_ACC,
        BEGINNING_STOCK
    FROM
        MOVE_OUT_AGG
    );
    """
        report_period = self.env['ir.config_parameter'].sudo().get_param('distrib.report_distrib_quantity_period',
                                                                         default='12')
        self.env.cr.execute(query, {'report_period': int(report_period)})
