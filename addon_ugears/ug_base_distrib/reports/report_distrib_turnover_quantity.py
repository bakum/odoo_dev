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
    # product_tmpl_id = fields.Many2one('product.template', readonly=True)
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
    # cartoon_id = fields.Many2one('distrib.packages.sizes', 'Cartoon', readonly=True)
    start_price_total = fields.Float(string='Beginning Amount', readonly=True)
    start_price_total_acc = fields.Float(string='Beginning Amount (acc)', readonly=True,
                                         groups="ug_base_distrib.group_distrib_manager")
    price_total = fields.Float(string='Ending Amount', readonly=True)
    price_total_acc = fields.Float(string='Ending Amount (acc)', readonly=True,
                                   groups="ug_base_distrib.group_distrib_manager")
    full_name = fields.Char(string='Product Full Name', readonly=True)
    barcode = fields.Char(string='EAN', readonly=True)
    default_code = fields.Char(string='Product Code', readonly=True)
    # barcode = fields.Char(related='product_id.barcode',
    #                       depends=['product_id'],
    #                       help="International Article Number used for product identification.")
    # default_code = fields.Char(related='product_id.default_code', depends=['product_id'])

    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_distrib_turnover_quantity')
        query = """
        -- CREATE OR REPLACE FUNCTION public.first_agg (anyelement, anyelement)
        --   RETURNS anyelement
        --   LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE AS
        -- 'SELECT $1';
        -- 
        -- DROP AGGREGATE IF EXISTS public.first(anyelement);
        -- CREATE AGGREGATE public.first(anyelement) (
        --   SFUNC = public.first_agg
        -- , STYPE = anyelement
        -- , PARALLEL = safe
        -- );
        -- 
        -- 
        -- CREATE OR REPLACE FUNCTION public.last_agg (anyelement, anyelement)
        --   RETURNS anyelement
        --   LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE AS
        -- 'SELECT $2';
        -- 
        -- DROP AGGREGATE IF EXISTS public.last(anyelement);
        -- CREATE AGGREGATE public.last(anyelement) (
        --   SFUNC = public.last_agg
        -- , STYPE = anyelement
        -- , PARALLEL = safe
        -- );
        CREATE or REPLACE VIEW report_distrib_turnover_quantity AS (
        WITH
	DISTRIBUTOR AS (
		SELECT
			DIST.ID,
			DIST.REGION_ID
		FROM
			DISTRIB_DISTRIBUTORS AS DIST
	),
	ALL_DM_MONTHS (
		ID,
		PRODUCT_ID,
		PERIOD,
		STATE,
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
			'month' AS PERIOD,
			'forecast' AS STATE,
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
			DISTRIB_QUANT_TOTALS H
			LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID = H.PRODUCT_ID
			LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID = PP.PRODUCT_TMPL_ID
			LEFT JOIN DISTRIBUTOR D ON D.ID = H.DISTRIB_ID
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
	) AS MAIN
	LEFT JOIN PRODUCT_PRODUCT PP ON PP.ID = MAIN.PRODUCT_ID
	LEFT JOIN PRODUCT_TEMPLATE PT ON PT.ID = PP.PRODUCT_TMPL_ID
	where period='month'
    );
    """
        report_period = self.env['ir.config_parameter'].sudo().get_param('distrib.report_distrib_quantity_period',
                                                                         default='12')
        self.env.cr.execute(query, {'report_period': int(report_period)})
