/** @odoo-module **/

import {Component, useState, xml} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import {registry} from "@web/core/registry";
import {PDFViewer} from "../PDFViewer/PDFViewer";
import {WordViewer} from "../WordViewer/WordViewer";

export class SemanticSearch extends Component {
    static components = {PDFViewer, WordViewer};

    highlight(text, query) {
        const escaped = query.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&');
        const pattern = new RegExp(escaped, "gi");
        return text.replace(pattern, (match) => `<mark>${match}</mark>`);
    }

    onKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.search();
        }
    }

    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            query: "",
            results: [],
            summary: "",
            isLoading: false,
            showLimit: 4,  // Сколько карточек показывать
            expanded: false,
            tokenCount: null,
            summarized: false,
            score_level: 0.85,
            pdfPanelVisible: false, // ← добавлено
            selectedResult: null, // ← для правой панели
            hasSearched: false,
        });
    }

    togglePdfPanel() {
        this.state.pdfPanelVisible = !this.state.pdfPanelVisible;
    }

    selectResult(res) {
        this.state.pdfPanelVisible = true; // Показываем панель PDF при выборе результата
        this.state.selectedResult = res;
    }

    toggleExpand() {
        this.state.expanded = !this.state.expanded;
    }

    async search() {
        this.state.isLoading = true;
        this.state.results = [];
        this.state.summary = "";
        this.state.tokenCount = null;
        this.state.selectedResult = null; // Сброс выбранного результата
        this.state.expanded = false; // Сброс состояния развёрнутости

        try {
            const raw = await this.rpc("/rag/search", {
                query: this.state.query,
                top_k: 10,
                threshold: parseFloat(this.state.score_level) || 0.80,
                summarized: this.state.summarized,
            });
            // Проверка на ошибку
            if (raw.error) {
                console.error("Search error:", raw.error);
                this.state.results = [];
                this.state.summary = raw.details || "No results found.";
                this.state.tokenCount = null;
                return;
            }
            this.state.results = raw.results.map(r => ({
                ...r,
                highlighted: this.highlight(r.text, this.state.query)
            }));
            this.state.summary = raw.summary;
            this.state.tokenCount = raw.tokens.total || null;
        } catch (error) {
            console.error("Search failed:", error);
            this.state.results = [];
            this.state.summary = "";
        } finally {
            this.state.isLoading = false;
            this.state.hasSearched = true;
        }
    }
}

SemanticSearch.template = "rag_search.SemanticSearch";
registry.category("actions").add("rag_search.search_widget", SemanticSearch);
