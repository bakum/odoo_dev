/** @odoo-module */

import { session } from "@web/session";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";

export class ImportInventoryController extends ListController {
    async onClickImport() {
        const activeIds = await this.model.orm.search(this.props.resModel, this.props.domain, {
            limit: session.active_ids_limit,
            context: this.props.context,
        });
        return this.actionService.doAction("ug_base_distrib.action_import_distrib_inventory", {
            additionalContext: {
                active_ids: activeIds,
            },
            onClose: () => {
                this.model.load();
            },
        });
    }
    OnDownload() {
        this.actionService.doAction({
            'type': 'ir.actions.act_url',
            'url': '/ug_base_distrib/static/xls/template_inventory_distrib.xlsx',
            'target': 'new'
        })
    }
    onClickInventoryAtDate() {
        const context = {
            active_model: this.props.resModel,
        };
        console.log('props',this.props)
        this.actionService.doAction({
            res_model: "distrib.quantity.history",
            views: [[false, "form"]],
            target: "new",
            type: "ir.actions.act_window",
            context,
        });
    }
}

export const ImportInventoryListView = {
    ...listView,
    Controller: ImportInventoryController,
    buttonTemplate: 'ImportDistribInventory.Buttons',
};

registry.category("views").add('import_distrib_inventory_list', ImportInventoryListView);