/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";
import {jsonrpc} from "@web/core/network/rpc_service";

options.registry.MazCategoriesOptions = options.Class.extend({

    // init() {
    //     this._super(...arguments);
    //     this.containerSelector = '> .container, > .container-fluid, > .o_container_small';
    //     this.selectTemplateWidgetName = 'masonry_template_opt';
    // },

    start() {
        let categoriesRow =  this.$target.find('#categories-row')
        if (categoriesRow) {
            jsonrpc('/categories', {}).then(data => {
                let html = ``
                data.forEach(category => {
                    html += ` <div class="col-lg-3 s_col_no_bgcolor pt16 pb16">
                                    <div class="card text-bg-white">
                                        <a href="/shop/category/${category.id}">
                                            <h5 class="card-header o_default_snippet_text">${category.name}</h5>
                                            <img class="card-img-top" src="data:image/*;base64,${category.image_512}"
                                                alt="" style="width: auto; height: 165px;"/>
                                             <div class="card-footer">
                                                <p class="card-text">${category.brand}</p>
                                            </div>
                                        </a>
                                    </div>
                                </div>`
                })
                categoriesRow.html(html)
            })
        }

    }

})

export default {
    MazCategoriesOptions: options.registry.MazCategoriesOptions,
};