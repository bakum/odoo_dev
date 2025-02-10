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
    start_product_qty = fields.Float(string='Start Quantity', readonly=True)
    product_qty = fields.Float(string='End Quantity', readonly=True)
    distrib_id = fields.Many2one('distrib.distributors', readonly=True, string='Distributor')
    categ_id = fields.Many2one('product.category', readonly=True, string='Category')
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    region_id = fields.Many2one('distrib.regions', "Region", readonly=True,
                                groups="ug_base_distrib.group_distrib_manager")
    cartoon_id = fields.Many2one('distrib.packages.sizes', 'Cartoon', readonly=True)
    start_price_total = fields.Float(string='Start Amount in Currency', readonly=True)
    start_price_total_acc = fields.Float(string='Start Amount in Currency Accounting', readonly=True,
                                         groups="ug_base_distrib.group_distrib_manager")
    price_total = fields.Float(string='Amount in Currency', readonly=True)
    price_total_acc = fields.Float(string='Amount in Currency Accounting', readonly=True,
                                   groups="ug_base_distrib.group_distrib_manager")
    full_name = fields.Char(string='Product Full Name', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_distrib_turnover_quantity')
        query = """
        CREATE or REPLACE VIEW report_distrib_turnover_quantity AS (
        WITH
	DISTRIBUTOR AS (
		SELECT
			DIST.ID,
			DIST.REGION_ID
		FROM
			DISTRIB_DISTRIBUTORS AS DIST
	),
	EXISTING_DM (
		ID,
		DISTRIB_ID,
		REGION_ID,
		PRODUCT_ID,
		TMPL_ID,
		PRODUCT_QTY,
		CURRENCY_ID,
		PRICE_UNIT,
		RATE,
		DATE,
		STATE
	) AS (
		SELECT
			DM.ID,
			DM.DISTRIB_ID,
			SOURCE.REGION_ID,
			DM.PRODUCT_ID,
			PT.ID,
			DM.BALANCE,
			DM.CURRENCY_ID,
			DM.PRICE_UNIT,
			DM.RATE,
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
		REGION_ID,
		PRODUCT_ID,
		TMPL_ID,
		PRODUCT_QTY,
		DATE,
		STATE,
		CURRENCY_ID,
		PRICE_UNIT,
		RATE
	) AS (
		SELECT
			Q.ID,
			Q.DISTRIB_ID,
			D.REGION_ID,
			Q.PRODUCT_ID,
			PP.PRODUCT_TMPL_ID,
			Q.QUANTITY,
			DATE.*::DATE,
			'forecast' AS STATE,
			Q.CURRENCY_ID,
			Q.PRICE_UNIT,
			Q.RATE
		FROM
			GENERATE_SERIES(
				DATE_TRUNC('MONTH', NOW() AT TIME ZONE 'utc')::DATE - INTERVAL '%(report_period)s month',
				DATE_TRUNC('MONTH', NOW() AT TIME ZONE 'utc')::DATE + INTERVAL '%(report_period)s month',
				'1 day'::INTERVAL
			) DATE,
			DISTRIB_QUANT Q
			LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID = Q.PRODUCT_ID
			LEFT JOIN DISTRIBUTOR D ON D.ID = Q.DISTRIB_ID
	),
	ALL_DM (
		ID,
		DISTRIB_ID,
		REGION_ID,
		PRODUCT_ID,
		TMPL_ID,
		PRODUCT_QTY,
		DATE,
		REAL_DATE,
		STATE,
		CURRENCY_ID,
		PRICE_UNIT,
		RATE
	) AS (
		SELECT
			ID,
			DISTRIB_ID,
			REGION_ID,
			PRODUCT_ID,
			TMPL_ID,
			PRODUCT_QTY,
			GENERATE_SERIES(
				DATE_TRUNC('MONTH', NOW() AT TIME ZONE 'utc')::DATE - INTERVAL '%(report_period)s month',
				DATE_TRUNC('MONTH', NOW() AT TIME ZONE 'utc')::DATE + INTERVAL '%(report_period)s month',
				'1 day'::INTERVAL
			)::DATE DATE,
			M.DATE::DATE AS REAL_DATE,
			'forecast' AS STATE,
			CURRENCY_ID,
			PRICE_UNIT,
			RATE
		FROM
			EXISTING_DM AS M
	),
	ALL_DM_DAYS (
		ID,
		PRODUCT_ID,
		STATE,
		DATE,
		PERIOD,
		DISTRIB_ID,
		REGION_ID,
		CATEG_ID,
		CARTOON_ID,
		QTY_IN_CARTOON,
		START_PRODUCT_QTY,
		PRODUCT_QTY,
		QTY_ALL_IN_CARTOON,
		CURRENCY_ID,
		PRICE_UNIT,
		RATE,
		START_PRICE_TOTAL,
		START_PRICE_TOTAL_ACC,
		PRICE_TOTAL,
		PRICE_TOTAL_ACC
	) AS (
		SELECT
			ID,
			PRODUCT_ID,
			STATE,
			DATE,
			PERIOD,
			DISTRIB_ID,
			REGION_ID,
			CATEG_ID,
			CARTOON_ID,
			QTY_IN_CARTOON,
			START_PRODUCT_QTY,
			PRODUCT_QTY,
			QTY_ALL_IN_CARTOON,
			CURRENCY_ID,
			ROUND(PRICE_UNIT::NUMERIC, 2) AS PRICE_UNIT,
			ROUND(RATE::NUMERIC, 5) AS RATE,
			ROUND((PRICE_UNIT * START_PRODUCT_QTY)::NUMERIC, 2) AS START_PRICE_TOTAL,
			ROUND(
				(PRICE_UNIT * START_PRODUCT_QTY * RATE)::NUMERIC,
				2
			) AS START_PRICE_TOTAL_ACC,
			ROUND((PRICE_UNIT * PRODUCT_QTY)::NUMERIC, 2) AS PRICE_TOTAL,
			ROUND((PRICE_UNIT * PRODUCT_QTY * RATE)::NUMERIC, 2) AS PRICE_TOTAL_ACC
		FROM
			(
				SELECT
					ROW_NUMBER() OVER (
						ORDER BY
							MAIN.ID
					) AS ID,
					MAIN.PRODUCT_ID,
					MAIN.STATE,
					MAIN.DATE,
					'days' AS PERIOD,
					MAIN.DISTRIB_ID,
					MAIN.REGION_ID,
					PT.CATEG_ID AS CATEG_ID,
					PT.CARTOON_ID AS CARTOON_ID,
					PT.QTY_IN_CARTOON AS QTY_IN_CARTOON,
					LAG(PRODUCT_QTY, 1) OVER (
						PARTITION BY
							DISTRIB_ID,
							PRODUCT_ID,
							STATE
						ORDER BY
							DATE
					) START_PRODUCT_QTY,
					MAIN.PRODUCT_QTY,
					CASE
						WHEN PT.QTY_IN_CARTOON = 0 THEN 0
						ELSE ROUND(
							(MAIN.PRODUCT_QTY / PT.QTY_IN_CARTOON)::NUMERIC,
							2
						)
					END AS QTY_ALL_IN_CARTOON,
					CURRENCY_ID,
					PRICE_UNIT,
					RATE
				FROM
					(
						SELECT
							MIN(FORECAST_QTY.ID) AS ID,
							PRODUCT_ID,
							TMPL_ID PRODUCT_TMPL_ID,
							STATE,
							DATE,
							DISTRIB_ID,
							REGION_ID,
							SUM(PRODUCT_QTY) AS PRODUCT_QTY,
							CURRENCY_ID,
							AVG(PRICE_UNIT) AS PRICE_UNIT,
							AVG(RATE) AS RATE
						FROM
							(
								SELECT
									M.ID,
									M.REGION_ID,
									M.PRODUCT_ID,
									M.TMPL_ID,
									CASE
										WHEN M.PRODUCT_QTY < 0 THEN 'out'
										WHEN M.PRODUCT_QTY > 0 THEN 'in'
									END AS STATE,
									M.DATE::DATE AS DATE,
									DISTRIB_ID,
									PRODUCT_QTY,
									CURRENCY_ID,
									PRICE_UNIT,
									RATE
								FROM
									EXISTING_DM M
								UNION ALL
								SELECT
									ID,
									REGION_ID,
									PRODUCT_ID,
									TMPL_ID,
									STATE,
									DATE,
									DISTRIB_ID,
									PRODUCT_QTY,
									CURRENCY_ID,
									PRICE_UNIT,
									RATE
								FROM
									QUANTS
								UNION ALL
								SELECT
									ID,
									REGION_ID,
									PRODUCT_ID,
									TMPL_ID,
									STATE,
									DATE,
									DISTRIB_ID,
									CASE
										WHEN REAL_DATE > DATE THEN - PRODUCT_QTY
										ELSE 0
									END AS PRODUCT_QTY,
									CURRENCY_ID,
									PRICE_UNIT,
									RATE
								FROM
									ALL_DM
							) AS FORECAST_QTY
						GROUP BY
							PRODUCT_ID,
							TMPL_ID,
							STATE,
							DATE,
							DISTRIB_ID,
							REGION_ID,
							CURRENCY_ID
					) AS MAIN
					LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID = MAIN.PRODUCT_TMPL_ID
			) AS QR
	),
	ALL_DM_MONTHS (
		ID,
		PRODUCT_ID,
		STATE,
		DATE,
		PERIOD,
		DISTRIB_ID,
		REGION_ID,
		CATEG_ID,
		CARTOON_ID,
		CURRENCY_ID,
		QTY_IN_CARTOON,
		START_PRODUCT_QTY,
		PRODUCT_QTY,
		QTY_ALL_IN_CARTOON,
		PRICE_UNIT,
		RATE,
		START_PRICE_TOTAL,
		START_PRICE_TOTAL_ACC,
		PRICE_TOTAL,
		PRICE_TOTAL_ACC
	) AS (
		SELECT
			ID,
			PRODUCT_ID,
			STATE,
			DATE,
			PERIOD,
			DISTRIB_ID,
			REGION_ID,
			CATEG_ID,
			CARTOON_ID,
			CURRENCY_ID,
			QTY_IN_CARTOON,
			START_PRODUCT_QTY,
			PRODUCT_QTY,
			QTY_ALL_IN_CARTOON,
			ROUND(PRICE_UNIT::NUMERIC, 2) AS PRICE_UNIT,
			ROUND(RATE::NUMERIC, 5) AS RATE,
			ROUND((PRICE_UNIT * START_PRODUCT_QTY)::NUMERIC, 2) AS START_PRICE_TOTAL,
			ROUND(
				(PRICE_UNIT * START_PRODUCT_QTY * RATE)::NUMERIC,
				2
			) AS START_PRICE_TOTAL_ACC,
			ROUND((PRICE_UNIT * PRODUCT_QTY)::NUMERIC, 2) AS PRICE_TOTAL,
			ROUND((PRICE_UNIT * PRODUCT_QTY * RATE)::NUMERIC, 2) AS PRICE_TOTAL_ACC
		FROM
			(
				SELECT
					MIN(ID) AS ID,
					PRODUCT_ID,
					STATE,
					DATE_TRUNC('MONTH', DATE)::DATE AS DATE,
					'month' AS PERIOD,
					DISTRIB_ID,
					REGION_ID,
					CATEG_ID,
					CARTOON_ID,
					CURRENCY_ID,
					QTY_IN_CARTOON,
					SUM(
						CASE
							WHEN DATE_TRUNC('MONTH', DATE)::DATE = DATE THEN START_PRODUCT_QTY
							ELSE 0
						END
					) AS START_PRODUCT_QTY,
					SUM(
						CASE
							WHEN DATE_TRUNC('month', DATE)::DATE + INTERVAL '1 month' - INTERVAL '1 day' = DATE THEN PRODUCT_QTY
							ELSE 0
						END
					) AS PRODUCT_QTY,
					SUM(
						CASE
							WHEN DATE_TRUNC('MONTH', DATE)::DATE = DATE THEN QTY_ALL_IN_CARTOON
							ELSE 0
						END
					) AS QTY_ALL_IN_CARTOON,
					AVG(PRICE_UNIT) AS PRICE_UNIT,
					AVG(RATE) AS RATE
				FROM
					ALL_DM_DAYS
				GROUP BY
					PRODUCT_ID,
					STATE,
					DATE_TRUNC('MONTH', DATE)::DATE,
					DISTRIB_ID,
					REGION_ID,
					CATEG_ID,
					CARTOON_ID,
					CURRENCY_ID,
					QTY_IN_CARTOON
			) AS ALL_MONTH
	),
	ALL_DM_YEARS (
		ID,
		PRODUCT_ID,
		STATE,
		DATE,
		PERIOD,
		DISTRIB_ID,
		REGION_ID,
		CATEG_ID,
		CARTOON_ID,
		CURRENCY_ID,
		QTY_IN_CARTOON,
		START_PRODUCT_QTY,
		PRODUCT_QTY,
		QTY_ALL_IN_CARTOON,
		PRICE_UNIT,
		RATE,
		START_PRICE_TOTAL,
		START_PRICE_TOTAL_ACC,
		PRICE_TOTAL,
		PRICE_TOTAL_ACC
	) AS (
		SELECT
			ID,
			PRODUCT_ID,
			STATE,
			DATE,
			PERIOD,
			DISTRIB_ID,
			REGION_ID,
			CATEG_ID,
			CARTOON_ID,
			CURRENCY_ID,
			QTY_IN_CARTOON,
			START_PRODUCT_QTY,
			PRODUCT_QTY,
			QTY_ALL_IN_CARTOON,
			ROUND(PRICE_UNIT::NUMERIC, 2) AS PRICE_UNIT,
			ROUND(RATE::NUMERIC, 5) AS RATE,
			ROUND((PRICE_UNIT * START_PRODUCT_QTY)::NUMERIC, 2) AS START_PRICE_TOTAL,
			ROUND(
				(PRICE_UNIT * START_PRODUCT_QTY * RATE)::NUMERIC,
				2
			) AS START_PRICE_TOTAL_ACC,
			ROUND((PRICE_UNIT * PRODUCT_QTY)::NUMERIC, 2) AS PRICE_TOTAL,
			ROUND((PRICE_UNIT * PRODUCT_QTY * RATE)::NUMERIC, 2) AS PRICE_TOTAL_ACC
		FROM
			(
				SELECT
					MIN(ID) AS ID,
					PRODUCT_ID,
					STATE,
					DATE_TRUNC('YEAR', DATE)::DATE AS DATE,
					'year' AS PERIOD,
					DISTRIB_ID,
					REGION_ID,
					CATEG_ID,
					CARTOON_ID,
					CURRENCY_ID,
					QTY_IN_CARTOON,
					SUM(
						CASE
							WHEN DATE_TRUNC('YEAR', DATE)::DATE = DATE THEN START_PRODUCT_QTY
							ELSE 0
						END
					) AS START_PRODUCT_QTY,
					SUM(
						CASE
							WHEN DATE_TRUNC('YEAR', DATE)::DATE + INTERVAL '1 YEAR' - INTERVAL '1 day' = DATE THEN PRODUCT_QTY
							ELSE 0
						END
					) AS PRODUCT_QTY,
					SUM(QTY_ALL_IN_CARTOON) AS QTY_ALL_IN_CARTOON,
					AVG(PRICE_UNIT) AS PRICE_UNIT,
					AVG(RATE) AS RATE
				FROM
					ALL_DM_DAYS
				GROUP BY
					PRODUCT_ID,
					STATE,
					DATE_TRUNC('YEAR', DATE)::DATE,
					DISTRIB_ID,
					REGION_ID,
					CATEG_ID,
					CARTOON_ID,
					CURRENCY_ID,
					QTY_IN_CARTOON
			) AS ALL_YEAR
	)
SELECT
	MAIN.ID,
	PRODUCT_ID,
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
	CURRENCY_ID,
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
			QTY_IN_CARTOON,
			START_PRODUCT_QTY,
			PRODUCT_QTY,
			QTY_ALL_IN_CARTOON,
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
			STATE,
			PERIOD,
			DATE,
			DISTRIB_ID,
			REGION_ID,
			CATEG_ID,
			CARTOON_ID,
			CURRENCY_ID,
			QTY_IN_CARTOON,
			START_PRODUCT_QTY,
			PRODUCT_QTY,
			QTY_ALL_IN_CARTOON,
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
			QTY_IN_CARTOON,
			START_PRODUCT_QTY,
			PRODUCT_QTY,
			QTY_ALL_IN_CARTOON,
			START_PRICE_TOTAL,
			START_PRICE_TOTAL_ACC,
			PRICE_TOTAL,
			PRICE_TOTAL_ACC
		FROM
			ALL_DM_YEARS AS MM
	) AS MAIN
	LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID = MAIN.PRODUCT_ID
	LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID = PP.PRODUCT_TMPL_ID
WHERE
	STATE = 'forecast'
    );
    """
        report_period = self.env['ir.config_parameter'].sudo().get_param('distrib.report_distrib_quantity_period',
                                                                         default='12')
        self.env.cr.execute(query, {'report_period': int(report_period)})
