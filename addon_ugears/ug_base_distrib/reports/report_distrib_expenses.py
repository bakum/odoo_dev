from odoo import models, fields, tools


class ReportDistribExpenses(models.Model):
    _name = 'report.distrib.expenses'
    _auto = False
    _description = 'Distributor Expenses Report'

    _depends = {
        'distrib.marketing.expenses.line': ['date', 'distrib_id', 'expense_id', 'state'],
    }

    date = fields.Date(string='Date', readonly=True)
    distrib_id = fields.Many2one('distrib.distributors', readonly=True, string='Distributor')
    expense_id = fields.Many2one('distrib.types.marketings', string='Type of Expense', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    region_id = fields.Many2one('distrib.regions', "Region", readonly=True)
    expense_total = fields.Float(string='Total', readonly=True)
    expense_total_acc = fields.Float(string='Total in currency of accounting', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_distrib_expenses')
        query = """
        CREATE or REPLACE VIEW report_distrib_expenses AS (
        WITH
        DISTRIBUTOR (ID, REGION_ID, CURRENCY_ID) AS (
            SELECT
                DIST.ID,
                DIST.REGION_ID,
                PP.CURRENCY_ID
            FROM
                DISTRIB_DISTRIBUTORS AS DIST
                LEFT JOIN PRODUCT_PRICELIST PP ON PP.ID = DIST.PRICELIST_ID
        ),
        EXPENSES_EM (
            ID,
            DISTRIB_ID,
            REGION_ID,
            CURRENCY_ID,
            EXPENSE_ID,
            DATE,
            STATE,
            EXPENSE_TOTAL,
            EXPENSE_TOTAL_ACC
        ) AS (
            SELECT
                DML.ID,
                SOURCE.ID AS DISTRIB_ID,
                SOURCE.REGION_ID,
                SOURCE.CURRENCY_ID AS CURRENCY_ID,
                DML.EXPENSE_ID,
                MONTH::DATE AS DATE,
                STATE,
                EXPENSE_TOTAL,
                ROUND((EXPENSE_TOTAL * RATE)::NUMERIC, 2) AS EXPENSE_TOTAL_ACC
            FROM
                DISTRIB_MARKETING_EXPENSES_LINE AS DML
                LEFT JOIN DISTRIBUTOR SOURCE ON SOURCE.ID = DML.DISTRIB_ID
            WHERE
                DML.DISPLAY_TYPE IN ('expense')
                AND DML.EXPENSE_TOTAL != 0
                AND DML.STATE NOT IN ('draft', 'cancel')
        ),
        ALL_EXPENSES (
            ID,
            DISTRIB_ID,
            EXPENSE_ID,
            REGION_ID,
            CURRENCY_ID,
            REAL_DATE,
            DATE,
            STATE,
            EXPENSE_TOTAL,
            EXPENSE_TOTAL_ACC
        ) AS (
            SELECT
                ID,
                DISTRIB_ID,
                EXPENSE_ID,
                REGION_ID,
                CURRENCY_ID,
                M.DATE AS REAL_DATE,
                GENERATE_SERIES(
                    DATE_TRUNC('YEAR', NOW() AT TIME ZONE 'utc')::DATE - INTERVAL '%(report_period)s month',
                    DATE_TRUNC('YEAR', NOW() AT TIME ZONE 'utc')::DATE + INTERVAL '%(report_period)s month',
                    '1 month'::INTERVAL
                )::DATE DATE,
                'forecast' AS STATE,
                0,
                0
            FROM
                EXPENSES_EM M
        )
    SELECT
        ROW_NUMBER() OVER (
            ORDER BY
                MAIN.ID
        ) AS ID,
        DISTRIB_ID,
        REGION_ID,
        EXPENSE_ID,
        CURRENCY_ID,
        DATE,
        EXPENSE_TOTAL,
        EXPENSE_TOTAL_ACC
    FROM
        (
            SELECT
                MIN(ID) AS ID,
                DISTRIB_ID,
                REGION_ID,
                EXPENSE_ID,
                CURRENCY_ID,
                DATE,
                SUM(EXPENSE_TOTAL) AS EXPENSE_TOTAL,
                SUM(EXPENSE_TOTAL_ACC) AS EXPENSE_TOTAL_ACC
            FROM
                (
                    SELECT
                        ID,
                        DISTRIB_ID,
                        REGION_ID,
                        EXPENSE_ID,
                        CURRENCY_ID,
                        DATE,
                        STATE,
                        EXPENSE_TOTAL,
                        EXPENSE_TOTAL_ACC
                    FROM
                        EXPENSES_EM
                    UNION ALL
                    SELECT
                        ID,
                        DISTRIB_ID,
                        REGION_ID,
                        EXPENSE_ID,
                        CURRENCY_ID,
                        DATE,
                        STATE,
                        EXPENSE_TOTAL,
                        EXPENSE_TOTAL_ACC
                    FROM
                        ALL_EXPENSES
                ) AS MAIN
            GROUP BY
                DISTRIB_ID,
                REGION_ID,
                EXPENSE_ID,
                CURRENCY_ID,
                DATE
        ) AS MAIN
    );
    """
        report_period = self.env['ir.config_parameter'].sudo().get_param('distrib.report_distrib_quantity_period',
                                                                         default='12')
        self.env.cr.execute(query, {'report_period': int(report_period)})
