/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ChatMessage extends Component {
    static template = "llm_chat.ChatMessage";

    static props = {
        msg: Object,
    };
}