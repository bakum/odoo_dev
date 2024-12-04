/** @odoo-module */

import { registry } from "@web/core/registry"
import { KpiCard } from "./kpi_card/kpi_card"
import { ChartRenderer } from "./chart_renderer/chart_renderer"
const {Component, onWillStart, useRef, onWillDestroy, onUnMounted, useState} = owl

export class OwlDistribDashboard extends Component {
    setup(){

    }
}

OwlDistribDashboard.template = "owl.OwlSalesDashboard"
OwlDistribDashboard.components = { KpiCard, ChartRenderer }
registry.category("actions").add("owl.sales_dashboard", OwlDistribDashboard)