/** @odoo-module */

import {registry} from "@web/core/registry"
import {loadCSS, loadJS} from "@web/core/assets"
import {useService} from "@web/core/utils/hooks"
import {LogRenderer} from "./log_renderer/log_renderer";
import {RecordsRenderer} from "./records_renderer/records_renderer";
import {ProgressRenderer} from "./progress_renderer/progress_renderer";

const {Component, onWillStart, onMounted, onWillDestroy, useRef, useState} = owl

export class OwlRegionRel extends Component {

    setup() {
        this.state = useState({
            serverId: 0,
            log: {},
            logIsEmpty: true,
            exportStopped: true,
            begins_by_days: 0,
            begins_by_month: 0,
            total_by_days: 0,
            total_by_month: 0,
            progress_days: 0,
            progress_month: 0,
            diff_moments: 0,
        })
        this.file = useRef("file")
        this.rpc = useService("rpc")
        this.actionService = useService("action")
        this.orm = useService("orm")
        onWillStart(async () => {
            await loadJS("/ug_base_distrib/static/src/lib/filepond/filepond-plugin-file-validate-type.js")
            await loadJS("/ug_base_distrib/static/src/lib/filepond/filepond.min.js")
            await loadCSS("/ug_base_distrib/static/src/lib/filepond/filepond.min.css")
        })
        self = this
        onMounted(() => {
            // console.log("FilePond", FilePond)
            FilePond.registerPlugin(FilePondPluginFileValidateType);
            FilePond.setOptions({
                server: {
                    process: './filepond/process',
                    fetch: null,
                    revert: './filepond/revert',
                },
                stylePanelLayout: 'compact',
                // stylePanelAspectRatio: '4:1',
                onprocessfile: function (error, file) {
                    console.log("error", error)
                    if (error) {
                        self.actionService.doAction({
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': 'Process File',
                                'message': error.message,
                                'type': 'danger',
                                'sticky': false,
                            }
                        })
                    }
                    self.state.serverId = parseInt(file.serverId)
                    self.state.log = {}
                    self.state.logIsEmpty = true
                },
                onremovefile: (error, file) => {
                    self.state.serverId = 0
                }
            });
            this.pond = FilePond.create(this.file.el, {
                allowMultiple: false,
            })
        })

        onWillStart(async () => {
            await this.getTotals()
        })
        this.refreshIntervalId = setInterval(async () => {
            await this.getTotals()
        }, 5000)
        onWillDestroy(()=>{
            clearInterval(this.refreshIntervalId)
        })
    }

    async getBeginsTotals(){
        let domain = [['valid_rec', '=', false]]
        let current_date = moment().format('YYYY-MM-DD')
        this.state.begins_by_month = await this.orm.searchCount("distrib.point.relevance", [['date', '<', current_date]])
        this.state.begins_by_days = await this.orm.searchCount("distrib.quant.history", domain)

    }

    async getTotals(){
        let stop = moment()
        let domain = [['valid_rec', '=', false]]
        let current_date = moment().format('YYYY-MM-DD')
        this.state.total_by_month = await this.orm.searchCount("distrib.point.relevance", [['date', '<', current_date]])
        this.state.total_by_days = await this.orm.searchCount("distrib.quant.history", domain)
        this.state.progress_days = this.state.begins_by_days === 0 ? 0 : Math.round((1 - (this.state.total_by_days / this.state.begins_by_days )) * 100)
        this.state.progress_month = this.state.begins_by_month === 0 ? 0 : Math.round((1 - (this.state.total_by_month / this.state.begins_by_month)) * 100)
        if (this.start && this.start > 0)
            this.state.diff_moments = Math.round((stop - this.start)/1000)
        if (this.state.total_by_days === 0 && this.state.total_by_month === 0) {
            this.state.exportStopped = true
            this.state.begins_by_days = 0
            this.state.begins_by_month = 0
            this.state.progress_days = 0
            this.state.progress_month = 0
            if (this.start) this.start = 0
        }

    }

    async onRecalculate() {
        this.state.exportStopped = false
        this.state.diff_moments = 0
        this.start = moment()
        await this.getBeginsTotals()
        // this.refreshIntervalId = setInterval(async () => {
        //     await this.getTotals()
        // }, 5000)
        return await this.orm.call('distrib.distributors.move', 'run_recalculate_job', [false,true], {})
    }
    async onRecalculateOnceByMonth() {
        return await this.orm.call('distrib.distributors.move', 'run_recalculate_job_no_thread_once_by_month', [false], {})
    }

    onImport() {
        let params = {
            file_id: this.state.serverId,
        }
        this.rpc("/filepond/import", params).then((data) => {
            console.log("data.log", data.log)
            this.actionService.doAction({
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Import Results:',
                    'message': data.message,
                    'type': data.status === 'success' ? 'success' : 'danger',
                    'sticky': true,
                }
            })
            this.pond.removeFile({ revert: true });
            this.state.log = data.log
            this.state.logIsEmpty = false
        })
    }

    onDownload() {
        this.actionService.doAction({
            'type': 'ir.actions.act_url',
            'url': '/ug_base_distrib/static/xls/template_region.xlsx',
            'target': 'new'
        })
    }
}

OwlRegionRel.template = "region.OwlRegionRel"
OwlRegionRel.components = {LogRenderer, RecordsRenderer, ProgressRenderer}
registry.category("actions").add("region.import_relations", OwlRegionRel)