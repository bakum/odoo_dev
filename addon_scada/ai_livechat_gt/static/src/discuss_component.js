/** @odoo-module **/

import { Discuss } from "@mail/core/common/discuss";
import { patch } from "@web/core/utils/patch";
import { onWillStart } from "@odoo/owl";

/**
 * (V53) ИСПРАВЛЕНО: 'activeThread' не существует.
 *
 * Мы ПОЛНОСТЬЮ УДАЛЯЕМ проверку на 'activeThread.id === payload.channel_id'
 * по вашему предложению.
 *
 * Теперь, если JS получает 'ai_action', он немедленно 
 * его выполняет.
 */
patch(Discuss.prototype, {
    
    setup() {
        super.setup();
        this.busService = this.env.services.bus_service;
        
        onWillStart(() => {
            // (V49 - Код без изменений)
            this.busService.addEventListener("notification", this.onBusNotification.bind(this));
            const partnerChannel = String(this.env.services.user.partnerId);
            this.busService.addChannel(partnerChannel);
        });
    },

    /**
     * (V53) Обработчик пакета уведомлений
     */
    onBusNotification(event) {
        
        // console.log("AI Livechat (Bus V53): Received Event", event);
        const notifications = event.detail;
        
        if (!Array.isArray(notifications)) {
            return;
        }

        for (const notif of notifications) {
            
            const type = notif.type;
            const payload = notif.payload;

            // --- ЭТО И ЕСТЬ ИСПРАВЛЕНИЕ (V53) ---
            // Мы проверяем ТОЛЬКО 'type'
            
            if (type === 'ai_action' && payload && payload.action) {
                
                const actionData = payload.action;
                console.log("AI Action (Bus V53): EXECUTING ACTION (Check removed)", actionData);
                
                // Немедленно выполняем действие
                this.env.services.action.doAction(actionData);
                
                // (Мы выходим из цикла, так как действие выполнено)
                break;
            }
            // --- КОНЕЦ ИСПРАВЛЕНИЯ ---
        }
    },
});