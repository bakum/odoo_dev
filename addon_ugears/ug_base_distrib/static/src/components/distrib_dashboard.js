/** @odoo-module */

import {registry} from "@web/core/registry"
import {KpiCard} from "./kpi_card/kpi_card"
import {ChartRenderer} from "./chart_renderer/chart_renderer"

const {Component, onWillStart, useRef, onWillDestroy, onUnMounted, useState} = owl
import {useService} from "@web/core/utils/hooks"

export class OwlDistribDashboard extends Component {
    setup() {
        this.orm = useService("orm")
        this.actionService = useService("action")
        this.user = useService("user")
    }
}

OwlDistribDashboard.template = "owl.OwlSalesDashboard"
OwlDistribDashboard.components = {KpiCard, ChartRenderer}
registry.category("actions").add("owl.sales_dashboard", OwlDistribDashboard)