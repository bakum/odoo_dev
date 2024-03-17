/** @odoo-module */

import {registry} from "@web/core/registry"
import {KpiCard} from "./kpi_card/kpi_card"
import {ChartRenderer} from "./chart_renderer/chart_renderer"
import {loadJS} from "@web/core/assets"

const {Component, onWillStart, useRef, onMounted, useState} = owl
import {useService} from "@web/core/utils/hooks"

export class OwlWeightDashboard extends Component {

     getDates(){
        this.state.current_date = moment().subtract(this.state.period, 'days').format('YYYY-MM-DD')
        this.state.previous_date = moment().subtract(this.state.period * 2, 'days').format('YYYY-MM-DD')

         console.log(this.state.current_date)
         console.log(this.state.previous_date)
    }
    async getControllers() {
        let domain = [['active', '=', true]]
        const data = await this.orm.searchRead("nw.moxa", domain, ['id', 'name'])

        this.state.controllers = data
        this.state.current_controller = data.length > 0 ? data[0].id : 0
        // console.log("data", data)
    }

    async getWeight() {
        let domain = []
        if (this.state.current_controller > 0) {
             domain.push(['moxa_id','=', this.state.current_controller])
        }
        const data = await this.orm.searchRead("nw.weight", domain, ['id', 'nid','count','value1','value2'],{limit: 1, order:'write_date desc'})

        console.log("weight", data)
    }

    async getErrors() {
        let domain = []
        if (this.state.current_controller > 0) {
             domain.push(['moxa_id','=', this.state.current_controller])
        }
        const data = await this.orm.searchRead("nw.error", domain, ['id', 'nid','count','value'],{limit: 1, order:'write_date desc'})

        console.log("error", data)
    }

    setup() {
        this.state = useState({
            period: 90,
        })
        this.orm = useService("orm")
        this.actionService = useService("action")

        onWillStart(async () => {
            // await loadJS("/nw_server/static/src/components/moment/moment.min.js")
            this.getDates()
            await this.getControllers()
            await this.getWeight()
            await this.getErrors()

        })
    }


}

OwlWeightDashboard.template = "owl.OwlWeightDashboard"
OwlWeightDashboard.components = {KpiCard, ChartRenderer}

registry.category("actions").add("owl.weight_dashboard", OwlWeightDashboard)