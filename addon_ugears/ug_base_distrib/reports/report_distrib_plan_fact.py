from odoo import api, models, fields, tools


class ReportDistribPlanFact(models.Model):
    _name = 'report.distrib.plan.fact'
    _auto = False
    _description = 'Distributor Plan/Fact Report'

    _depends = {
        'product.product': ['product_tmpl_id'],
        'distrib.distributors.move.line': ['date', 'distrib_id', 'product_id', 'product_uom_qty', 'state'],
        'distrib.budget.move.line': ['date', 'distrib_id', 'product_id', 'product_uom_qty',
                                     'product_uom_qty2', 'product_uom_qty3', 'product_uom_qty4', 'product_uom_qty5',
                                     'product_uom_qty6', 'product_uom_qty7', 'product_uom_qty8', 'product_uom_qty9',
                                     'product_uom_qty10', 'product_uom_qty11', 'product_uom_qty12', ],
    }

    date = fields.Date(string='Date', readonly=True)
    month = fields.Date(string='Month', readonly=True)
    year = fields.Date(string='Year', readonly=True)
    distrib_id = fields.Many2one('distrib.distributors', readonly=True, string='Distributor')
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    full_name = fields.Char(string='Product Full Name', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    product_category_id = fields.Many2one('product.category', readonly=True, string='Category')
    state = fields.Selection([
        ('draft', "Draft"),
        ('done', "Locked"),
        ('cancel', "Cancelled"),
    ], string='State', readonly=True, groups="ug_base_distrib.group_distrib_manager")
    price_unit = fields.Float(string='Price', readonly=True, group_operator='avg',
                              groups="ug_base_distrib.group_distrib_manager")
    product_qty_plan = fields.Float(string='UGmodels Sell-In Plan, pcs', readonly=True)
    product_qty_fact = fields.Float(string='UGmodels Sell-In Fact, pcs', readonly=True)
    amount_plan = fields.Float(string='UGmodels Sell-In Plan, amount', readonly=True, groups="ug_base_distrib.group_distrib_manager")
    amount_fact = fields.Float(string='UGmodels Sell-In Fact, amount', readonly=True, groups="ug_base_distrib.group_distrib_manager")
    amount_plan_acc = fields.Float(string='UGmodels Sell-In Plan, amount (acc)', readonly=True,
                                   groups="ug_base_distrib.group_distrib_manager")
    amount_fact_acc = fields.Float(string='UGmodels Sell-In Fact, amount (acc)', readonly=True,
                                   groups="ug_base_distrib.group_distrib_manager")
    # barcode = fields.Char(related='product_id.barcode',
    #                       depends=['product_id'],
    #                       help="International Article Number used for product identification.")
    barcode = fields.Char(string='EAN', readonly=True)
    default_code = fields.Char(related='product_id.default_code', depends=['product_id'])
    # percentage = fields.Float(string='Variation, %', readonly=True)
    
    # @api.depends('product_qty_plan', 'product_qty_fact')
    # def _compute_percentage(self):
    #     for record in self:
    #         if record.product_qty_plan != 0:
    #             record.percentage = (record.product_qty_fact * 100 / record.product_qty_plan) * 100
    #         else:
    #             record.percentage = 0.0

    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_distrib_plan_fact')
        query = """
            CREATE or REPLACE VIEW report_distrib_plan_fact AS (
            WITH
	PLAN (
		ID,
		YEAR,
		MONTH,
		DISTRIB_ID,
		PRODUCT_ID,
		CURRENCY_ID,
		PRODUCT_CATEGORY_ID,
		STATE,
		PRICE_UNIT,
		PRODUCT_QTY_PLAN,
		PRODUCT_QTY_FACT,
		RATE
	) AS (
		SELECT
			ID,
			DATE_TRUNC('year', DATE AT TIME ZONE 'utc')::DATE AS YEAR,
			(
				CASE
					WHEN STEPS = 1 THEN DATE_TRUNC('year', DATE AT TIME ZONE 'utc')::DATE
					WHEN STEPS = 2 THEN DATE_TRUNC('year', DATE AT TIME ZONE 'utc')::DATE + INTERVAL '1 month'
					WHEN STEPS = 3 THEN DATE_TRUNC('year', DATE AT TIME ZONE 'utc')::DATE + INTERVAL '2 month'
					WHEN STEPS = 4 THEN DATE_TRUNC('year', DATE AT TIME ZONE 'utc')::DATE + INTERVAL '3 month'
					WHEN STEPS = 5 THEN DATE_TRUNC('year', DATE AT TIME ZONE 'utc')::DATE + INTERVAL '4 month'
					WHEN STEPS = 6 THEN DATE_TRUNC('year', DATE AT TIME ZONE 'utc')::DATE + INTERVAL '5 month'
					WHEN STEPS = 7 THEN DATE_TRUNC('year', DATE AT TIME ZONE 'utc')::DATE + INTERVAL '6 month'
					WHEN STEPS = 8 THEN DATE_TRUNC('year', DATE AT TIME ZONE 'utc')::DATE + INTERVAL '7 month'
					WHEN STEPS = 9 THEN DATE_TRUNC('year', DATE AT TIME ZONE 'utc')::DATE + INTERVAL '8 month'
					WHEN STEPS = 10 THEN DATE_TRUNC('year', DATE AT TIME ZONE 'utc')::DATE + INTERVAL '9 month'
					WHEN STEPS = 11 THEN DATE_TRUNC('year', DATE AT TIME ZONE 'utc')::DATE + INTERVAL '10 month'
					WHEN STEPS = 12 THEN DATE_TRUNC('year', DATE AT TIME ZONE 'utc')::DATE + INTERVAL '11 month'
				END
			)::DATE AS MONTH,
			DISTRIB_ID,
			PRODUCT_ID,
			CURRENCY_ID,
			PRODUCT_CATEGORY_ID,
			STATE,
			PRICE_UNIT,
			CASE
				WHEN STEPS = 1 THEN PRODUCT_UOM_QTY
				WHEN STEPS = 2 THEN PRODUCT_UOM_QTY2
				WHEN STEPS = 3 THEN PRODUCT_UOM_QTY3
				WHEN STEPS = 4 THEN PRODUCT_UOM_QTY4
				WHEN STEPS = 5 THEN PRODUCT_UOM_QTY5
				WHEN STEPS = 6 THEN PRODUCT_UOM_QTY6
				WHEN STEPS = 7 THEN PRODUCT_UOM_QTY7
				WHEN STEPS = 8 THEN PRODUCT_UOM_QTY8
				WHEN STEPS = 9 THEN PRODUCT_UOM_QTY9
				WHEN STEPS = 10 THEN PRODUCT_UOM_QTY10
				WHEN STEPS = 11 THEN PRODUCT_UOM_QTY11
				WHEN STEPS = 12 THEN PRODUCT_UOM_QTY12
			END AS PRODUCT_UOM_QTY,
			NULL AS FACT,
			RATE
		FROM
			DISTRIB_BUDGET_MOVE_LINE,
			GENERATE_SERIES(1, 12, 1) STEPS
		WHERE
			STATE IN ('done')
	),
	FACT (
		ID,
		YEAR,
		MONTH,
		DISTRIB_ID,
		PRODUCT_ID,
		CURRENCY_ID,
		PRODUCT_CATEGORY_ID,
		STATE,
		PRICE_UNIT,
		PRODUCT_QTY_PLAN,
		PRODUCT_QTY_FACT,
		RATE
	) AS (
		SELECT
			ID,
			DATE_TRUNC('year', DATE)::DATE AS YEAR,
			DATE_TRUNC('month', DATE)::DATE AS MONTH,
			DISTRIB_ID,
			PRODUCT_ID,
			CURRENCY_ID,
			PRODUCT_CATEGORY_ID,
			STATE,
			PRICE_UNIT,
			NULL,
			PRODUCT_UOM_QTY,
			RATE
		FROM
			DISTRIB_DISTRIBUTORS_MOVE_LINE ML
		WHERE
			ML.STATE IN ('done')
			AND ML.OPERATION = 'inc'
			AND NOT ML.IS_INVENTORY
	),
	PLAN_FACT (
		ID,
		YEAR,
		MONTH,
		DISTRIB_ID,
		PRODUCT_ID,
		CURRENCY_ID,
		PRODUCT_CATEGORY_ID,
		STATE,
		PRICE_UNIT,
		PRODUCT_QTY_PLAN,
		PRODUCT_QTY_FACT,
		RATE
	) AS (
		SELECT
			MIN(ID) AS ID,
			YEAR,
			MONTH,
			DISTRIB_ID,
			PRODUCT_ID,
			CURRENCY_ID,
			PRODUCT_CATEGORY_ID,
			STATE,
			MAX(PRICE_UNIT) AS PRICE_UNIT,
			SUM(PRODUCT_QTY_PLAN) AS PRODUCT_QTY_PLAN,
			SUM(PRODUCT_QTY_FACT) AS PRODUCT_QTY_FACT,
			AVG(RATE) AS RATE
		FROM
			(
				SELECT
					ID,
					YEAR,
					MONTH,
					DISTRIB_ID,
					PRODUCT_ID,
					CURRENCY_ID,
					PRODUCT_CATEGORY_ID,
					STATE,
					PRICE_UNIT,
					0 AS PRODUCT_QTY_PLAN,
					PRODUCT_QTY_FACT,
					RATE
				FROM
					FACT
				UNION ALL
				SELECT
					ID,
					YEAR,
					MONTH,
					DISTRIB_ID,
					PRODUCT_ID,
					CURRENCY_ID,
					PRODUCT_CATEGORY_ID,
					STATE,
					PRICE_UNIT,
					PRODUCT_QTY_PLAN,
					0,
					RATE
				FROM
					PLAN
			) AS MAIN
		GROUP BY
			YEAR,
			MONTH,
			DISTRIB_ID,
			PRODUCT_ID,
			CURRENCY_ID,
			PRODUCT_CATEGORY_ID,
			STATE
	)
SELECT
	ROW_NUMBER() OVER (
		ORDER BY
			MAIN.ID
	) AS ID,
	YEAR,
	MONTH,
	MONTH AS DATE,
	DISTRIB_ID,
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
	CURRENCY_ID,
	PRODUCT_CATEGORY_ID,
	STATE,
	PRICE_UNIT,
	PRODUCT_QTY_PLAN,
	PRODUCT_QTY_FACT,
	ROUND((PRICE_UNIT * PRODUCT_QTY_PLAN)::NUMERIC, 2) AS AMOUNT_PLAN,
	ROUND((PRICE_UNIT * PRODUCT_QTY_FACT)::NUMERIC, 2) AS AMOUNT_FACT,
	ROUND(
		(PRICE_UNIT * PRODUCT_QTY_PLAN * RATE)::NUMERIC,
		2
	) AS AMOUNT_PLAN_ACC,
	ROUND(
		(PRICE_UNIT * PRODUCT_QTY_FACT * RATE)::NUMERIC,
		2
	) AS AMOUNT_FACT_ACC,
	ROUND(RATE::NUMERIC, 5) AS RATE
FROM
	PLAN_FACT MAIN
	LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID = MAIN.PRODUCT_ID
	LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID = PP.PRODUCT_TMPL_ID
WHERE
	YEAR >= (
		DATE_TRUNC('year', NOW() AT TIME ZONE 'utc') - INTERVAL '%(report_period)s month'
	)::DATE
        );
        """
        report_period = self.env['ir.config_parameter'].sudo().get_param('distrib.report_distrib_quantity_period',
                                                                         default='12')
        self.env.cr.execute(query, {'report_period': int(report_period)})
