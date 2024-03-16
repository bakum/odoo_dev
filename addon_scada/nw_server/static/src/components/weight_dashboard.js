/** @odoo-module */

import { registry } from "@web/core/registry"
import { KpiCard } from "./kpi_card/kpi_card"
import { ChartRenderer } from "./chart_renderer/chart_renderer"
import { loadJS } from "@web/core/assets"
const { Component, onWillStart, useRef, onMounted } = owl

export class OwlWeightDashboard extends Component {
    setup(){

    }
}

OwlWeightDashboard.template = "owl.OwlWeightDashboard"
OwlWeightDashboard.components = { KpiCard, ChartRenderer }

registry.category("actions").add("owl.weight_dashboard", OwlWeightDashboard)