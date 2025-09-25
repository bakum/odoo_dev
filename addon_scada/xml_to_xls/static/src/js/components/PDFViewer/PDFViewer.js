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
        this.pdfDoc = null;   // <--- кэш для документа

        onWillStart(async () => {
            await loadJS("/xml_to_xls/static/lib/pdfjs/build/pdf.js");
            await loadJS("/xml_to_xls/static/lib/pdfjs/build/pdf.worker.js");

            if (!window.pdfjsLib?.GlobalWorkerOptions?.workerSrc) {
                window.pdfjsLib.GlobalWorkerOptions.workerSrc =
                    "/xml_to_xls/static/lib/pdfjs/build/pdf.worker.js";
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
    while (container.firstChild) {
        container.removeChild(container.firstChild);
    }

    try {
        // Загружаем PDF только если он ещё не загружен или URL сменился
        if (!this.pdfDoc || props.url !== this.currentUrl) {
            this.pdfDoc = await pdfjsLib.getDocument(props.url).promise;
            this.currentUrl = props.url;
            this.state.totalPages = this.pdfDoc.numPages;
        }
        const pdf = this.pdfDoc;
        // this.state.totalPages = pdf.numPages;

        const safePageNum = (this.state.currentPage >= 1 && this.state.currentPage <= pdf.numPages)
            ? this.state.currentPage
            : 1;

        // Контейнер для разворота
        const spread = document.createElement("div");
        spread.style.display = "flex";
        spread.style.justifyContent = "center";
        spread.style.gap = "20px"; // расстояние между страницами

        // функция рендера одной страницы
        const renderPage = async (pageNum) => {
            const page = await pdf.getPage(pageNum);
            const viewport = page.getViewport({scale: 1.2});

            const wrapper = document.createElement("div");
            wrapper.style.position = "relative";
            wrapper.style.display = "inline-block";
            wrapper.style.width = `${viewport.width}px`;
            wrapper.style.height = `${viewport.height}px`;

            const canvas = document.createElement("canvas");
            const context = canvas.getContext("2d");
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            wrapper.appendChild(canvas);

            const overlay = document.createElement("div");
            overlay.style.position = "absolute";
            overlay.style.top = "0";
            overlay.style.left = "0";
            overlay.style.width = "100%";
            overlay.style.height = "100%";
            overlay.style.pointerEvents = "none";
            wrapper.appendChild(overlay);

            await page.render({canvasContext: context, viewport}).promise;

            // Подсветка текста (работает только для первой страницы с charStart)
            if (props.charStart !== undefined && pageNum === safePageNum) {
                const textContent = await page.getTextContent();
                let totalChars = 0;
                for (const item of textContent.items) {
                    const len = item.str.length;
                    if (totalChars + len >= props.charStart) {
                        const span = document.createElement("span");
                        span.style.position = "absolute";
                        span.style.left = `${item.transform[4]}px`;
                        span.style.top = `${item.transform[5] - 10}px`;
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

            return wrapper;
        };

        // Рендерим текущую страницу
        const firstPage = await renderPage(safePageNum);
        spread.appendChild(firstPage);

        // Рендерим вторую страницу (если есть)
        if (safePageNum + 1 <= pdf.numPages) {
            const secondPage = await renderPage(safePageNum + 1);
            spread.appendChild(secondPage);
        }

        container.appendChild(spread);

    } catch (e) {
        console.error("Error loading PDF:", e);
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

PDFViewer.template = "xml_to_xls.PDFViewer";