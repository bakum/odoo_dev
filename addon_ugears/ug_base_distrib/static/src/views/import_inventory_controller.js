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
}

export const ImportInventoryListView = {
    ...listView,
    Controller: ImportInventoryController,
    buttonTemplate: 'ImportDistribInventory.Buttons',
};

registry.category("views").add('import_distrib_inventory_list', ImportInventoryListView);