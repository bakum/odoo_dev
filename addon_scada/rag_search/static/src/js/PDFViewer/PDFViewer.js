/** @odoo-module **/

import {loadJS} from "@web/core/assets"
import {Component, useRef, useState, onMounted, onWillStart, onWillUpdateProps} from "@odoo/owl";

export class PDFViewer extends Component {
    static props = {
        url: String,
        pageNumber: {type: Number, optional: true},
        charStart: {type: Number, optional: true},
    };

    setup() {
        this.viewerRef = useRef("pdfViewer");
        this.state = useState({
            currentPage: this.props.pageNumber || 1,
            totalPages: 1,
        });

        onWillStart(async () => {
            await loadJS("/rag_search/static/src/js/lib/pdfjs/build/pdf.js");
            await loadJS("/rag_search/static/src/js/lib/pdfjs/build/pdf.worker.js");

            if (!window.pdfjsLib?.GlobalWorkerOptions?.workerSrc) {
                window.pdfjsLib.GlobalWorkerOptions.workerSrc =
                    "/rag_search/static/src/js/lib/pdfjs/build/pdf.worker.js";
            }
        });

        onMounted(() => this.loadPDF());

        onWillUpdateProps(async (nextProps) => {
            // console.log(nextProps)
            // Если URL или pageNumber изменились
            if (nextProps.url !== this.props.url) {
                // Новый документ: сбрасываем состояние и загружаем сначала
                this.state.currentPage = nextProps.pageNumber || 1;
                this.state.totalPages = 1;
                await this.loadPDF(nextProps); // <--- передаём явно
            } else if (nextProps.pageNumber !== this.props.pageNumber) {
                // Смена страницы для того же документа
                if (typeof nextProps.pageNumber === "number" && nextProps.pageNumber >= 1) {
                    this.state.currentPage = nextProps.pageNumber;
                    await this.loadPDF(nextProps); // <--- передаём явно
                }
            }
        });
    }

    async loadPDF(props = this.props) {
        if (!props.url) return;

        const pdfjsLib = window.pdfjsLib;
        const container = this.viewerRef.el;
        container.innerHTML = "";

        try {
            const pdf = await pdfjsLib.getDocument(props.url).promise;
            this.state.totalPages = pdf.numPages;

            const safePageNum = (this.state.currentPage >= 1 && this.state.currentPage <= pdf.numPages)
                ? this.state.currentPage
                : 1;

            const page = await pdf.getPage(safePageNum);
            const viewport = page.getViewport({scale: 1.0});

            // Обертка с relative-позицией
            const wrapper = document.createElement("div");
            wrapper.style.position = "relative";
            wrapper.style.display = "inline-block";
            wrapper.style.width = `${viewport.width}px`;
            wrapper.style.height = `${viewport.height}px`;

            // Canvas PDF
            const canvas = document.createElement("canvas");
            const context = canvas.getContext("2d");
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            wrapper.appendChild(canvas);

            // Overlay div для выделения
            const overlay = document.createElement("div");
            overlay.style.position = "absolute";
            overlay.style.top = "0";
            overlay.style.left = "0";
            overlay.style.width = "100%";
            overlay.style.height = "100%";
            overlay.style.pointerEvents = "none"; // ← чтобы не перекрывал мышь
            wrapper.appendChild(overlay);

            container.appendChild(wrapper);

            await page.render({canvasContext: context, viewport}).promise;

            // Подсветка текста
            if (props.charStart !== undefined) {
                const textContent = await page.getTextContent();
                let totalChars = 0;
                for (const item of textContent.items) {
                    const len = item.str.length;
                    if (totalChars + len >= props.charStart) {
                        const span = document.createElement("span");
                        span.style.position = "absolute";
                        span.style.left = `${item.transform[4]}px`;
                        span.style.top = `${item.transform[5] - 10}px`; // немного выше
                        span.style.background = "rgba(255, 255, 0, 0.6)";
                        span.style.padding = "1px 2px";
                        span.style.fontSize = "12px";
                        span.textContent = item.str;

                        overlay.appendChild(span);
                        span.scrollIntoView({behavior: "smooth", block: "center"});
                        break;
                    }
                    totalChars += len;
                }
            }
        } catch (e) {
            console.error("Ошибка загрузки PDF:", e);
        }
    }

    async goToPage(offset) {
        const nextPage = this.state.currentPage + offset;
        if (nextPage >= 1 && nextPage <= this.state.totalPages) {
            this.state.currentPage = nextPage;
            await this.loadPDF();
        }
    }
}

PDFViewer.template = "rag_search.PDFViewer";