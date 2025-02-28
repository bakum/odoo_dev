/** @odoo-module */

import {registry} from "@web/core/registry"
import {loadJS, loadCSS} from "@web/core/assets"
import {useService} from "@web/core/utils/hooks"
import {LogRenderer} from "./log_renderer/log_renderer";

const {Component, onWillStart, onMounted, useRef, useState} = owl

export class OwlRegionRel extends Component {

    setup() {
        this.state = useState({
            serverId: 0,
            log: {},
            logIsEmpty: true
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
    }

    async onRecalculate() {
        return await this.orm.call('distrib.distributors.move', 'run_recalculate_job', [false,false], {})
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
OwlRegionRel.components = {LogRenderer}
registry.category("actions").add("region.import_relations", OwlRegionRel)