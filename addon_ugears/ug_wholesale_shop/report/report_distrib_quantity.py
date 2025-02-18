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
	),
	ALL_DAYS AS (
		SELECT
			MIN(ID) AS ID,
			PRODUCT_ID,
			DISTRIB_ID,
			REGION_ID,
			CURRENCY_ID,
			CATEG_ID,
			CARTOON_ID,
			ROUND(AVG(PRICE_UNIT)::NUMERIC, 2) PRICE_UNIT,
			ROUND(AVG(RATE)::NUMERIC, 5) RATE,
			QTY_IN_CARTOON,
			DATE,
			LAST (
				CASE
					WHEN CURR_DATE <> DATE THEN PRODUCT_QTY
					ELSE START_PRODUCT_QTY
				END
			) AS START_PRODUCT_QTY,
			LAST (PRODUCT_QTY) PRODUCT_QTY,
			LAST (
				CASE
					WHEN CURR_DATE <> DATE THEN PRICE_TOTAL
					ELSE START_PRICE_TOTAL
				END
			) AS START_PRICE_TOTAL,
			LAST (
				CASE
					WHEN CURR_DATE <> DATE THEN PRICE_TOTAL_ACC
					ELSE START_PRICE_TOTAL_ACC
				END
			) AS START_PRICE_TOTAL_ACC,
			LAST (PRICE_TOTAL) PRICE_TOTAL,
			LAST (PRICE_TOTAL_ACC) PRICE_TOTAL_ACC
		FROM
			(
				SELECT
					ID,
					PRODUCT_ID,
					DISTRIB_ID,
					REGION_ID,
					CURRENCY_ID,
					CATEG_ID,
					CARTOON_ID,
					PRICE_UNIT,
					RATE,
					QTY_IN_CARTOON,
					CURR_DATE,
					NEXT_DATE,
					GENERATE_SERIES(
						CURR_DATE::DATE,
						NEXT_DATE::DATE - INTERVAL '1 day',
						'1 day'::INTERVAL
					)::DATE DATE,
					START_PRODUCT_QTY,
					PRODUCT_QTY,
					START_PRICE_TOTAL,
					START_PRICE_TOTAL_ACC,
					PRICE_TOTAL,
					PRICE_TOTAL_ACC
				FROM
					(
						SELECT
							Q1.ID,
							Q1.PRODUCT_ID,
							Q1.DISTRIB_ID,
							Q1.REGION_ID,
							Q1.CURRENCY_ID,
							Q1.CATEG_ID,
							Q1.CARTOON_ID,
							Q1.PRICE_UNIT,
							Q1.RATE,
							q1.QTY_IN_CARTOON,
							Q1.DATE AS CURR_DATE,
							COALESCE(
								Q2.DATE,
								DATE_TRUNC('year', NOW() AT TIME ZONE 'utc') + INTERVAL '%(report_period)s month'
							)::DATE AS NEXT_DATE,
							Q1.START_PRODUCT_QTY,
							Q1.PRODUCT_QTY,
							Q1.START_PRICE_TOTAL,
							Q1.START_PRICE_TOTAL_ACC,
							Q1.PRICE_TOTAL,
							Q1.PRICE_TOTAL_ACC
						FROM
							QTT_REMAINS Q1
							LEFT JOIN QTT_REMAINS Q2 ON Q1.PRODUCT_ID = Q2.PRODUCT_ID
							AND Q1.DISTRIB_ID = Q2.DISTRIB_ID
							AND Q1.DATE::DATE < Q2.DATE::DATE
					) AS MAIN
				ORDER BY
					DISTRIB_ID,
					PRODUCT_ID,
					DATE
			) AS QQQ
		GROUP BY
			PRODUCT_ID,
			DISTRIB_ID,
			REGION_ID,
			CURRENCY_ID,
			CATEG_ID,
			CARTOON_ID,
			QTY_IN_CARTOON,
			DATE
		ORDER BY
			DISTRIB_ID,
			PRODUCT_ID,
			DATE
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
		ELSE ROUND((PRODUCT_QTY / QTY_IN_CARTOON)::NUMERIC, 2)
	END AS QTY_ALL_IN_CARTOON
FROM
	ALL_DAYS
    );
    """
        report_period = self.env['ir.config_parameter'].sudo().get_param('distrib.report_distrib_quantity_period',
                                                                         default='12')
        self.env.cr.execute(query, {'report_period': int(report_period)})


