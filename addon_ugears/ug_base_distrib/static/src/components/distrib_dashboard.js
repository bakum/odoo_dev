/** @odoo-module */

import {registry} from "@web/core/registry"
import {KpiCard} from "./kpi_card/kpi_card"
import {ChartRenderer} from "./chart_renderer/chart_renderer"

const {Component, onWillStart, useRef, onWillDestroy, onUnMounted, useState} = owl
import {useService} from "@web/core/utils/hooks"

const fillPallets = (totalBoxNumber, boxHeight, boxWeight, boxesPerLayer, palletMaxHeight, palletMaxWeight) => {
    let maxBoxesByHeight = Math.floor(palletMaxHeight / boxHeight) * boxesPerLayer;
    let maxBoxesByWeight = Math.floor(palletMaxWeight / boxWeight);
    let maxBoxesPerPallet = Math.min(maxBoxesByHeight, maxBoxesByWeight);
    let fullPalletsCount = Math.floor(totalBoxNumber / maxBoxesPerPallet);
    let palletsCount = Math.ceil(totalBoxNumber / maxBoxesPerPallet);
    let lastPalletBoxes = totalBoxNumber - fullPalletsCount * maxBoxesPerPallet;
    let buildPallet = function (number) {
        let palletLayers = [];
        for (let rest = number; rest > 0; rest -= boxesPerLayer) {
            palletLayers.push(Math.min(rest, boxesPerLayer))
        }
        return palletLayers;
    }
    let pallets = [];
    let fullPallet = buildPallet(maxBoxesPerPallet);
    for (let i = 0; i < fullPalletsCount; i++) {
        pallets.push(fullPallet);
    }
    if (lastPalletBoxes > 0)
        pallets.push(buildPallet(lastPalletBoxes));

    return {
        count: palletsCount,
        palletsLayouts: pallets
    }
}

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