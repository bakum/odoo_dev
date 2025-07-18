/** @odoo-module **/

import { loadJS } from "@web/core/assets";
import {Component, useRef, onMounted, onWillStart, onWillUpdateProps} from "@odoo/owl";

export class WordViewer extends Component {
    static props = {
        url: String,
    };

    setup() {
        this.containerRef = useRef("wordContainer");

        onWillStart(async () => {
            await loadJS("/rag_search/static/src/js/lib/mammoth/mammoth.browser.min.js");
        });

        onMounted(() => this.loadWord());

        onWillUpdateProps(async (nextProps) => {
            if (nextProps.url !== this.props.url) {
                await this.loadWord(nextProps)
            }
        })
    }

    async loadWord(props = this.props) {
        if (!props.url) return;

        const container = this.containerRef.el;
        container.innerHTML = "";

        try {
            const response = await fetch(props.url);
            const blob = await response.blob();

            const arrayBuffer = await blob.arrayBuffer();
            window.mammoth.convertToHtml({ arrayBuffer }).then((result) => {
                container.innerHTML = result.value;
            }).catch((e) => {
                console.error("Ошибка отображения Word-файла:", e);
                container.innerHTML = "<div class='text-danger'>Ошибка при отображении документа</div>";
            });
        } catch (e) {
            console.error("Ошибка загрузки Word:", e);
            container.innerHTML = "<div class='text-danger'>Невозможно загрузить документ</div>";
        }
    }
}

WordViewer.template = "rag_search.WordViewer";
