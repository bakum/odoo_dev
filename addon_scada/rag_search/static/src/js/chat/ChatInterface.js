/** @odoo-module **/

import {Component, useRef, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useAutoFocus, useAutoResizeTextarea, useAutoScrollBottom, useLLM} from "../hooks/hooks";
import {ChatMessage} from "./components/ChatMessage";

let nextId = 1;

export class ChatInterface extends Component {
    static template = "llm_chat.ChatInterface";
    static components = { ChatMessage };

    setup() {
        this.state = useState({
            input: "",
            messages: [], // [{id, text, sender: 'user' | 'bot'}]
        });

        this.textarea = useRef("textarea");
        this.chatMessages = useRef("chatMessages");
        useAutoFocus(this.textarea)
        this.autoResize = useAutoResizeTextarea(this.textarea);
        useAutoScrollBottom(this.chatMessages, [this.state.messages.length]);

        this.llm = useLLM('/rag/chat');
    }

    async sendMessage() {
        const input = this.state.input.trim();
        if (!input) return;

        // Добавим сообщение от пользователя
        const userMsg = {id: nextId++, sender: "user", text: input};
        const botMsg = {id: nextId++, sender: "assistant", text: ""};

        this.state.messages.push(userMsg, botMsg);
        this.state.input = "";
        this.autoResize();

        await this.llm.stream({
            prompt: input,
            onChunk: (chunk) => {
                botMsg.text += chunk;
                this.state.messages = [...this.state.messages];
            }
        });

        if (this.llm.state.error) {
            botMsg.text += "\n⚠️ Error: " + this.llm.state.error;
            this.state.messages = [...this.state.messages];
        }
    }
}

registry.category("actions").add("rag_search.chat_widget", ChatInterface);
