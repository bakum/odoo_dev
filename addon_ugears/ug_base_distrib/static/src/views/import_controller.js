/** @odoo-module */

import { session } from "@web/session";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";

export class ImportMoveController extends ListController {
    async onClickImport() {
        const activeIds = await this.model.orm.search(this.props.resModel, this.props.domain, {
            limit: session.active_ids_limit,
            context: this.props.context,
        });
        return this.actionService.doAction("ug_base_distrib.action_import_distrib_move", {
            additionalContext: {
                active_ids: activeIds,
            },
            onClose: () => {
                this.model.load();
            },
        });
    }

    OnDownloadIn() {
        // this.actionService.doAction({
        //     'type': 'ir.actions.act_url',
        //     'url': '/ug_base_distrib/static/xls/template_incomes_distrib.xlsx',
        //     'target': 'new'
        // })
        return this.actionService.doAction("ug_base_distrib.report_export_products_in_xls", {
           additionalContext: {
               move_type: 'in'
            },
        });
    }
    OnDownloadOut() {
        // this.actionService.doAction({
        //     'type': 'ir.actions.act_url',
        //     'url': '/ug_base_distrib/static/xls/template_sales_distrib.xlsx',
        //     'target': 'new'
        // })
        return this.actionService.doAction("ug_base_distrib.report_export_products_out_xls", {
           additionalContext: {
               move_type: 'out'
            },
        });
    }
}

export const ImportMoveListView = {
    ...listView,
    Controller: ImportMoveController,
    buttonTemplate: 'ImportDistribMove.Buttons',
};

registry.category("views").add('import_distrib_move_list', ImportMoveListView);