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
    product_tmpl_id = fields.Many2one('product.template', readonly=True)
    product_category_id = fields.Many2one('product.category', readonly=True, string='Category')
    beginning_stock = fields.Float(string='Beginning stock, pcs', readonly=True, group_operator='sum')
    sell_in = fields.Float(string='Sell-In, pcs', readonly=True, group_operator='sum')
    sell_in_curr = fields.Float(string='Sell-In Currency', readonly=True, group_operator='sum')
    sell_in_acc = fields.Float(string='Sell-In Currency Accounting', readonly=True, group_operator='sum')

    balance = fields.Float(string='pcs', readonly=True)
    price_total = fields.Float(string='Amount in Currency', readonly=True)
    price_total_acc = fields.Float(string='Amount in Currency Accounting', readonly=True)
    full_name = fields.Char(string='Product Full Name', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_distrib_sales')
        query = """
        CREATE or REPLACE VIEW report_distrib_sales AS (
    WITH
	QTT_REMAINS (
		ID,
		PRODUCT_ID,
		STATE,
		DATE,
		DISTRIB_ID,
		CATEG_ID,
		PRODUCT_QTY
	) AS (
		SELECT
			ID,
			PRODUCT_ID,
			STATE,
			DATE,
			DISTRIB_ID,
			CATEG_ID,
			PRODUCT_QTY
		FROM
			REPORT_DISTRIB_QUANTITY QTT
		WHERE
			STATE = 'forecast'
			AND DATE_TRUNC('Month', DATE)::DATE = DATE
		ORDER BY
			DATE
	),
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
	MOVE_OUT (
		ID,
		DISTRIB_ID,
		CURRENCY_ID,
		CHANNEL_ID,
		PRODUCT_ID,
		PRODUCT_TMPL_ID,
		PRODUCT_CATEGORY_ID,
		STATE,
		OPERATION,
		PRICE_TOTAL,
		DATE,
		BALANCE,
		PRICE_TOTAL_ACC
	) AS (
		SELECT
			MIN(DML.ID),
			DISTRIB_ID,
			CURRENCY_ID,
			C.ID,
			PRODUCT_ID,
			PP.PRODUCT_TMPL_ID,
			PRODUCT_CATEGORY_ID,
			STATE,
			OPERATION,
			SUM(
				CASE
					WHEN C.ID = DML.CHANNEL_ID THEN PRICE_TOTAL
					ELSE null
				END
			) AS PRICE_TOTAL,
			DATE_TRUNC('MONTH', DATE)::DATE,
			SUM(
				CASE
					WHEN C.ID = DML.CHANNEL_ID THEN BALANCE
					ELSE null
				END
			) AS BALANCE,
			SUM(
				CASE
					WHEN C.ID = DML.CHANNEL_ID THEN PRICE_TOTAL * RATE
					ELSE null
				END
			) AS BALANCE_ACC
		FROM
			DISTRIB_DISTRIBUTORS_MOVE_LINE DML
			LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID = DML.PRODUCT_ID,
			CHANNELS C
		WHERE
			DML.STATE IN ('done')
			AND NOT DML.IS_INVENTORY
			AND DML.DISPLAY_TYPE = 'product'
			AND DML.OPERATION = 'out'
		GROUP BY
			DISTRIB_ID,
			CURRENCY_ID,
			C.ID,
			PRODUCT_ID,
			PP.PRODUCT_TMPL_ID,
			PRODUCT_CATEGORY_ID,
			STATE,
			OPERATION,
			DATE_TRUNC('MONTH', DATE)::DATE
	),
	MOVE_IN (
		ID,
		DISTRIB_ID,
		CURRENCY_ID,
		PRODUCT_ID,
		PRODUCT_TMPL_ID,
		PRODUCT_CATEGORY_ID,
		STATE,
		OPERATION,
		PRICE_TOTAL,
		DATE,
		BALANCE,
		PRICE_TOTAL_ACC
	) AS (
		SELECT
			MIN(DML.ID),
			DISTRIB_ID,
			CURRENCY_ID,
			PRODUCT_ID,
			PP.PRODUCT_TMPL_ID,
			PRODUCT_CATEGORY_ID,
			STATE,
			OPERATION,
			SUM(PRICE_TOTAL),
			DATE_TRUNC('MONTH', DATE)::DATE AS DATE,
			SUM(BALANCE),
			SUM(PRICE_TOTAL * RATE)
		FROM
			DISTRIB_DISTRIBUTORS_MOVE_LINE DML
			LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID = DML.PRODUCT_ID
		WHERE
			DML.STATE IN ('done')
			AND NOT DML.IS_INVENTORY
			AND DML.DISPLAY_TYPE = 'product'
			AND DML.OPERATION = 'inc'
		GROUP BY
			DISTRIB_ID,
			CURRENCY_ID,
			PRODUCT_ID,
			PP.PRODUCT_TMPL_ID,
			PRODUCT_CATEGORY_ID,
			STATE,
			OPERATION,
			DATE_TRUNC('MONTH', DATE)::DATE
	),
	MOVE_IN_ALL (
		ID,
		DISTRIB_ID,
		CURRENCY_ID,
		CHANNEL_ID,
		PRODUCT_ID,
		PRODUCT_TMPL_ID,
		PRODUCT_CATEGORY_ID,
		STATE,
		OPERATION,
		PRICE_TOTAL,
		DATE,
		BALANCE,
		PRICE_TOTAL_ACC,
		BEGINNING_STOCK
	) AS (
		SELECT
			MI.ID,
			MI.DISTRIB_ID,
			CURRENCY_ID,
			C.ID,
			MI.PRODUCT_ID,
			PRODUCT_TMPL_ID,
			PRODUCT_CATEGORY_ID,
			MI.STATE,
			OPERATION,
			CASE
				WHEN C.ROW_NUM = 1 THEN PRICE_TOTAL
				ELSE null
			END,
			MI.DATE,
			CASE
				WHEN C.ROW_NUM = 1 THEN BALANCE
				ELSE null
			END,
			CASE
				WHEN C.ROW_NUM = 1 THEN PRICE_TOTAL_ACC
				ELSE null
			END,
			CASE
				WHEN C.ROW_NUM = 1 THEN Q.PRODUCT_QTY
				ELSE null
			END AS BEGINNING_STOCK
		FROM
			MOVE_IN MI
			LEFT JOIN QTT_REMAINS Q ON Q.DISTRIB_ID = MI.DISTRIB_ID
			AND Q.PRODUCT_ID = MI.PRODUCT_ID
			AND Q.DATE = MI.DATE,
			CHANNELS C
	),
	MOVE_ALL (
		ID,
		DATE,
		DISTRIB_ID,
		CURRENCY_ID,
		CHANNEL_ID,
		PRODUCT_ID,
		PRODUCT_TMPL_ID,
		PRODUCT_CATEGORY_ID,
		SELL_IN,
		SELL_IN_CURR,
		SELL_IN_ACC,
		PRICE_TOTAL,
		BALANCE,
		PRICE_TOTAL_ACC,
		BEGINNING_STOCK
	) AS (
		SELECT
			MIN(ID),
			DATE,
			DISTRIB_ID,
			CURRENCY_ID,
			CHANNEL_ID,
			PRODUCT_ID,
			PRODUCT_TMPL_ID,
			PRODUCT_CATEGORY_ID,
			MAX(SELL_IN),
			MAX(SELL_IN_CURR),
			MAX(SELL_IN_ACC),
			SUM(PRICE_TOTAL),
			SUM(BALANCE),
			SUM(PRICE_TOTAL_ACC),
			MAX(BEGINNING_STOCK)
		FROM
			(
				SELECT
					ID,
					DATE,
					DISTRIB_ID,
					CURRENCY_ID,
					CHANNEL_ID,
					PRODUCT_ID,
					PRODUCT_TMPL_ID,
					PRODUCT_CATEGORY_ID,
					STATE,
					OPERATION,
					PRICE_TOTAL AS SELL_IN_CURR,
					BALANCE AS SELL_IN,
					PRICE_TOTAL_ACC AS SELL_IN_ACC,
					null AS PRICE_TOTAL,
					null AS BALANCE,
					null AS PRICE_TOTAL_ACC,
					BEGINNING_STOCK
				FROM
					MOVE_IN_ALL
				UNION ALL
				SELECT
					ID,
					DATE,
					DISTRIB_ID,
					CURRENCY_ID,
					CHANNEL_ID,
					PRODUCT_ID,
					PRODUCT_TMPL_ID,
					PRODUCT_CATEGORY_ID,
					STATE,
					OPERATION,
					null,
					null,
					null,
					PRICE_TOTAL,
					- BALANCE,
					PRICE_TOTAL_ACC,
					null
				FROM
					MOVE_OUT
			) AS MAIN
		GROUP BY
			DATE,
			DISTRIB_ID,
			CURRENCY_ID,
			CHANNEL_ID,
			PRODUCT_ID,
			PRODUCT_TMPL_ID,
			PRODUCT_CATEGORY_ID
	)
SELECT
	ROW_NUMBER() OVER (
		ORDER BY
			MAIN.ID
	) AS ID,
	DATE,
	DISTRIB_ID,
	CURRENCY_ID,
	CHANNEL_ID,
	PRODUCT_ID,
	PRODUCT_TMPL_ID,
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
	(
		SELECT
			MA.ID,
			DATE.*::DATE,
			DISTRIB_ID,
			CURRENCY_ID,
			CHANNEL_ID,
			PRODUCT_ID,
			MA.PRODUCT_TMPL_ID,
			CONCAT(
				PT.NAME -> 'en_US',
				'/',
				PP.BARCODE,
				'/',
				PP.DEFAULT_CODE
			) AS FULL_NAME,
			PRODUCT_CATEGORY_ID,
			CASE
				WHEN DATE.*::DATE = MA.DATE THEN SELL_IN
				ELSE null
			END AS SELL_IN,
			CASE
				WHEN DATE.*::DATE = MA.DATE THEN SELL_IN_CURR
				ELSE null
			END AS SELL_IN_CURR,
			CASE
				WHEN DATE.*::DATE = MA.DATE THEN SELL_IN_ACC
				ELSE null
			END AS SELL_IN_ACC,
			CASE
				WHEN DATE.*::DATE = MA.DATE THEN PRICE_TOTAL
				ELSE null
			END AS PRICE_TOTAL,
			CASE
				WHEN DATE.*::DATE = MA.DATE THEN BALANCE
				ELSE null
			END AS BALANCE,
			CASE
				WHEN DATE.*::DATE = MA.DATE THEN PRICE_TOTAL_ACC
				ELSE null
			END AS PRICE_TOTAL_ACC,
			CASE
				WHEN DATE.*::DATE = MA.DATE THEN BEGINNING_STOCK
				ELSE null
			END AS BEGINNING_STOCK
		FROM
			MOVE_ALL MA
			LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID = MA.PRODUCT_ID
			LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID = MA.PRODUCT_TMPL_ID,
			GENERATE_SERIES(
				DATE_TRUNC('YEAR', NOW() AT TIME ZONE 'utc')::DATE - INTERVAL '%(report_period)s month',
				DATE_TRUNC('YEAR', NOW() AT TIME ZONE 'utc')::DATE + INTERVAL '%(report_period)s month',
				'1 month'::INTERVAL
			) DATE
	) AS MAIN
    );
    """
        report_period = self.env['ir.config_parameter'].sudo().get_param('distrib.report_distrib_quantity_period',
                                                                         default='12')
        self.env.cr.execute(query, {'report_period': int(report_period)})
