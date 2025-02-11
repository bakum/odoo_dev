/** @odoo-module */

import {registry} from "@web/core/registry"
import {KpiCard} from "./kpi_card/kpi_card"
import {ChartRenderer} from "./chart_renderer/chart_renderer"

const {Component, onWillStart, useRef, onWillDestroy, onUnMounted, useState} = owl
import {useService} from "@web/core/utils/hooks"
import {browser} from "@web/core/browser/browser"
import {routeToUrl} from "@web/core/browser/router_service"

export class OwlDistribDashboard extends Component {
    async getDistributors() {
        let domain = []
        let manager = await this.user.hasGroup('ug_base_distrib.group_distrib_manager'),
            user = await this.user.hasGroup('ug_base_distrib.group_distrib_user'),
            restricted = !manager && user
        if (restricted) {
            let user_data = await this.orm.searchRead("res.users", [['id', '=', this.user.userId]], ['id', 'distrib_id'], {
                limit: 1,
            })
            domain.push(['id', '=', user_data[0].distrib_id[0] || 0])
        }
        const data = await this.orm.searchRead("distrib.distributors", domain, ['id', 'name'])
        if (restricted && data.length > 0) {
            this.state.distributor = data[0].id
        }
        this.state.restricted = restricted
        this.state.distributors = data
    }

    async setup() {
        this.state = useState({
            period: 30,
            distributor: 0,
            restricted: true,
        })
        this.orm = useService("orm")
        this.actionService = useService("action")
        this.user = useService("user")

        const old_chartjs = document.querySelector('script[src="/web/static/lib/Chart/Chart.js"]')
        const router = useService("router")
        if (old_chartjs) {
            let root_menu = 'menu_distrib_root';
            let menu = 'ir.model.data';
            let menu_ids = await this.orm.searchRead(menu, [['name', '=', root_menu]], ['res_id'])
            let {search, hash} = router.current
            search.old_chartjs = old_chartjs != null ? "0" : "1"
            hash.action = this.props.actionId
            if (menu_ids) {
                if (menu_ids.length > 0) {
                    let menu_id = menu_ids[0]
                    hash.menu_id = menu_id.res_id
                }
            }
            browser.location.href = browser.location.origin + routeToUrl(router.current)
            return
        }

        onWillStart(async () => {
            this.getDates()
            await this.getDistributors()
        })
    }
    async onRecalculate() {
        this.getDates()
        // await this.getQuotations()
        // await this.getOrders()
        //
        // await this.getTopProducts()
        // await this.getTopSalesPeople()
        // await this.getMonthlySales()
        // await this.getPartnerOrders()
    }

    async onChangePeriod() {
        await this.onRecalculate()
    }

    async onChangeDistributor() {
        await this.onRecalculate()
    }

    getDates() {
        this.state.current_date = moment().subtract(this.state.period, 'days').format('L')
        this.state.previous_date = moment().subtract(this.state.period * 2, 'days').format('L')
    }
}

OwlDistribDashboard.template = "owl.OwlSalesDashboard"
OwlDistribDashboard.components = {KpiCard, ChartRenderer}
registry.category("actions").add("owl.sales_dashboard", OwlDistribDashboard)