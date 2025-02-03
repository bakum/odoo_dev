/** @odoo-module */

import {registry} from "@web/core/registry"
import {KpiCard} from "./kpi_card/kpi_card"
import {ChartRenderer} from "./chart_renderer/chart_renderer"

const {Component, onWillStart, useRef, onWillDestroy, onUnMounted, useState} = owl
import {useService} from "@web/core/utils/hooks"
import {browser} from "@web/core/browser/browser"
import {routeToUrl} from "@web/core/browser/router_service"

export class OwlDistribDashboard extends Component {
    async setup() {
        this.orm = useService("orm")
        this.actionService = useService("action")
        this.user = useService("user")

        const old_chartjs = document.querySelector('script[src="/web/static/lib/Chart/Chart.js"]')
        const router = useService("router")
        // console.log("router.current", router.current)
        if (old_chartjs) {
            let tag = 'owl.sales_dashboard';
            let root_menu = 'menu_distrib_root';
            let model = 'ir.actions.client';
            const ids = await this.orm.searchRead(model, [['tag', '=', tag]], ['id'], {
                limit: 1,
            })
            const menu_ids = await this.orm.searchRead('ir.model.data', [['name', '=', root_menu]], ['res_id'], {
                limit: 1,
            })

            if (ids.length > 0) {
                let action_id = ids[0]
                let menu_id = menu_ids[0]
                let {search, hash} = router.current
                search.old_chartjs = old_chartjs != null ? "0" : "1"
                hash.action = action_id.id
                hash.menu_id = menu_id.res_id
                // console.log("router.current", router.current)
                browser.location.href = browser.location.origin + routeToUrl(router.current)
            }
        }
    }
}

OwlDistribDashboard.template = "owl.OwlSalesDashboard"
OwlDistribDashboard.components = {KpiCard, ChartRenderer}
registry.category("actions").add("owl.sales_dashboard", OwlDistribDashboard)