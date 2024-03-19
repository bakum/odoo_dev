/** @odoo-module */

import {registry} from "@web/core/registry"
import {KpiCard} from "./kpi_card/kpi_card"
import {ChartRenderer} from "./chart_renderer/chart_renderer"
import {loadJS} from "@web/core/assets"

const {Component, onWillStart, useRef, onWillDestroy, onUnMounted, useState} = owl
import {useService} from "@web/core/utils/hooks"

export class OwlWeightDashboard extends Component {


    getDates() {
        this.state.current_date = moment().subtract(this.state.period, 'days').format('YYYY-MM-DD')
        this.state.previous_date = moment().subtract(this.state.period * 2, 'days').format('YYYY-MM-DD')
    }

    async getControllers() {
        let domain = [['active', '=', true]]
        const data = await this.orm.searchRead("nw.moxa", domain, ['id', 'name'])

        this.state.controllers = data
        // this.state.current_controller = data.length > 0 ? data[0].id : 0
        // console.log("data", data)
    }

    async getWeight() {
        let domain = [],
            null_data = {
                "id": Number(this.state.current_controller),
                "nid" : "none",
                "count": 0,
                "value1": 0,
                "value2": 0,
            }
        if (this.state.current_controller > 0) {
            domain.push(['moxa_id', '=', Number(this.state.current_controller)])
            domain.push(['count', '>', 1])
        }
        if (this.state.period > 0) {
            domain.push(['write_date', '>', this.state.current_date])
        }
        const data = await this.orm.searchRead("nw.weight", domain, ['id', 'nid', 'count', 'value1', 'value2'], {
            limit: 1,
            order: 'write_date desc'
        })
        const data_group = await this.orm.readGroup("nw.weight", domain, ["value1:sum", "value2:sum", "count:max"], [])
        const data_last = await this.orm.call('nw.weight','compute_current_weight',["",this.state.current_controller],{})

        this.state.weight_data = data.length > 0 ? data[0] : null_data
        // console.log("current_controller", this.state.current_controller)
        console.log("weight", data_last)
        // console.log("domain", domain)
    }

    async getErrors() {
        let domain = [],
            null_data = {
                "id": Number(this.state.current_controller),
                "nid" : "none",
                "count": 0,
                "value": 0,
            }
        if (this.state.current_controller > 0) {
            domain.push(['moxa_id', '=', Number(this.state.current_controller)])
        }
        const data = await this.orm.searchRead("nw.error", domain, ['id', 'nid', 'count', 'value'], {
            limit: 1,
            order: 'write_date desc'
        })
        this.state.error_data = data.length > 0 ? data[0] : null_data
        // console.log("error", data)
    }

    async onChangePeriod() {
        this.getDates()
        await this.getWeight()
        await this.getErrors()
    }

    async onChangeController() {
        await this.getWeight()
        await this.getErrors()
    }

    setup() {
        this.state = useState({
            period: 0,
            current_controller: 0,
            weight_data: {},
            error_data: {},
            weight: {
                value:10,
                percentage:6,
            }
        })
        this.orm = useService("orm")
        this.actionService = useService("action")

        this.refreshIntervalId = setInterval(async () => {
            await this.getWeight()
            await this.getErrors()
        }, 5000)

        onWillStart(async () => {
            // await loadJS("/nw_server/static/src/components/moment/moment.min.js")
            this.getDates()
            await this.getControllers()
            await this.getWeight()
            await this.getErrors()

        })

        onWillDestroy(()=>{
            clearInterval(this.refreshIntervalId)
        })
    }


}

OwlWeightDashboard.template = "owl.OwlWeightDashboard"
OwlWeightDashboard.components = {KpiCard, ChartRenderer}

registry.category("actions").add("owl.weight_dashboard", OwlWeightDashboard)
