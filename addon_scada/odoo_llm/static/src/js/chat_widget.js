/** @odoo-module **/

import {Component, onMounted, onWillUnmount, useEffect, useRef, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";

export class ChatWidget extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.orm = useService("orm");
        this.messageRef = useRef("messages");
        this.cardRef = useRef("card");
        this.state = useState({
            // session_id: this.props.action.context.params.res_id,
            header: '',
            inputText: "",
            messages: [],
            sessions: [],
            isLoading: false,
        });

        onMounted(async () => {
            await this.loadSessions();
            this.adjustMessageHeight()
            window.addEventListener("resize", this.adjustMessageHeight);
            // Пример: можно подгрузить историю сообщений при старте
        });

        useEffect(() => {
            this.scrollToBottom();
        }, () => [this.state.messages]);

        onWillUnmount(() => {
            window.removeEventListener("resize", this.adjustMessageHeight);
        });
    }

    getHeaderText() {
        return this.state.header || _t("New conversation");
    }

    scrollToBottom() {
        const el = this.messageRef.el;
        if (el) {
            el.scrollTop = el.scrollHeight;
        }
    }

    adjustMessageHeight = () => {
        const refEl = this.messageRef.el;
        const chatCard = refEl?.closest(".card");

        if (refEl && chatCard) {
            const totalHeight = chatCard.clientHeight;
            const footerHeight = chatCard.querySelector(".card-footer")?.offsetHeight || 0;
            const headerHeight = chatCard.querySelector(".card-header")?.offsetHeight || 0;

            const scrollAreaHeight = totalHeight - footerHeight - headerHeight;
            refEl.style.height = scrollAreaHeight + "px";
        }
    }

    async loadSessions() {
        this.state.sessions = await this.orm.searchRead("llm.chat.session", [], ["id", "name"], {
            order: "id desc", limit: 10
        });
    }

    async loadSessionMessages(el) {
        // console.log(el.target.id)
        const sessionId = parseInt(el.target.id)
        this.state.session_id = sessionId;
        const session = this.state.sessions.find((s) => s.id === sessionId);
        this.state.header = session?.name || '';

        const messages = await this.orm.searchRead("llm.chat.message", [['session_id', '=', sessionId]], ["id", "author", "content"]);
        this.state.messages = messages;
    }

    async deleteSession(el) {
        if (!confirm("Are you sure you want to delete this session?")) return;
        const sessionId = parseInt(el.target.id)

        try {
            await this.orm.unlink("llm.chat.session", [sessionId]);

            // Удаляем из списка на клиенте
            this.state.sessions = this.state.sessions.filter(s => s.id !== sessionId);

            // Если удалили текущую активную сессию — сбрасываем
            if (this.state.session_id === sessionId) {
                this.state.session_id = null;
                this.state.header = "";
                this.state.messages = [];
            }
            await this.loadSessions()
        } catch (error) {
            console.error("Failed to delete session:", error);
            alert("⚠ Не удалось удалить сессию.");
        }
    }

    async createNewSession(newHeader) {
        const now = new Date();
        const shortText = newHeader.trim().split(/\s+/).slice(0, 6).join(" ");
        const dateStr = now.toLocaleDateString() + " " + now.toLocaleTimeString().slice(0, 5);
        const title = `${dateStr} — ${shortText}`;
        const record = await this.orm.create("llm.chat.session", [{name: title}]);
        this.state.session_id = record[0];
        this.state.header = title;
    }

    async sendMessage() {
        const text = this.state.inputText.trim();
        if (!text) return;
        if (!this.state.session_id) {
            await this.createNewSession(text)
            await this.loadSessions()
        }
        const id = Date.now().toString() + Math.random().toString(16).slice(2);

        this.state.messages.push({id, author: "user", content: text});
        this.state.inputText = "";
        this.state.isLoading = true;

        try {
            const response = await this.rpc("/llm/chat/send", {
                session_id: this.state.session_id,
                text: text,
            });
            const botId = Date.now().toString() + Math.random().toString(16).slice(2);
            this.state.messages.push({id: botId, author: 'bot', content: response.bot.content});
        } catch (error) {
            const errId = Date.now().toString() + Math.random().toString(16).slice(2);
            this.state.messages.push({id: errId, author: 'bot', content: '⚠ Ошибка запроса.'});
        } finally {
            this.state.isLoading = false;
        }
    }

    onKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }

    onNewSessionClick() {
        this.state.session_id = null;
        this.state.header = "";
        this.state.messages = [];
    }

    updateInput(ev) {
        this.state.inputText = ev.target.value;
    }
}

ChatWidget.template = "odoo_llm.ChatWidget";
registry.category("actions").add("odoo_llm.chat_widget", ChatWidget);