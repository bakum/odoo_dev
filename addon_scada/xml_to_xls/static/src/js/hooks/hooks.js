/** @odoo-module **/

import {onMounted, reactive, useEffect} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

export function useAutoFocus(ref) {
    onMounted(() => {
        if (ref.el) {
            ref.el.focus();
        }
    });
}

export function useAutoScrollBottom(ref, deps = []) {
    useEffect(
        () => {
            if (ref.el) {
                ref.el.scrollTop = ref.el.scrollHeight;
            }
        },
        () => deps
    );
}