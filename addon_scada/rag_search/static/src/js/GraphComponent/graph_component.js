/** @odoo-module **/

import { Component, onMounted, useRef } from "@odoo/owl";

export class GraphComponent extends Component {
    setup() {
        this.containerRef = useRef("graphContainer");

        onMounted(() => {
            const cy = cytoscape({
                container: this.containerRef.el,
                elements: this.props.elements,
                style: [
                    {
                        selector: "node",
                        style: {
                            label: "data(label)",
                            "text-valign": "center",
                            "color": "#000",
                            "background-color": "#90cdf4",
                            "border-width": 2,
                            "border-color": "#3182ce",
                        },
                    },
                    {
                        selector: "edge",
                        style: {
                            label: "data(label)",
                            "curve-style": "bezier",
                            "target-arrow-shape": "triangle",
                            "width": 2,
                            "line-color": "#aaa",
                            "target-arrow-color": "#aaa",
                        },
                    },
                ],
                layout: { name: "cose" },
            });
        });
    }

    static props = {
        elements: Array,
    };

    static template = "rag_search.GraphComponent";
}
