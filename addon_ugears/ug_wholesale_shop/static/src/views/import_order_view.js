/** @odoo-module */

import { listView } from "@web/views/list/list_view";
import { ImportOrderController } from "./import_order_controller";
import { registry } from "@web/core/registry";

export const ImportOrderListView = {
    ...listView,
    Controller: ImportOrderController,
    buttonTemplate: 'ImportOrder.Buttons',
};

registry.category("views").add('import_order_list', ImportOrderListView);