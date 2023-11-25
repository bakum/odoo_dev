/** @odoo-module */

import { listView } from "@web/views/list/list_view";
import { ResCurrencyListController } from "./res_currency_list_controller";
import { registry } from "@web/core/registry";

export const ResCurrencyListView = {
    ...listView,
    Controller: ResCurrencyListController,
    buttonTemplate: 'ResCurrencyRates.Buttons',
};

registry.category("views").add('res_currency_list', ResCurrencyListView);
