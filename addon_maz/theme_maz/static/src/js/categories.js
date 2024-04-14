/** @odoo-module */

import PublicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";


export const MazCategories = PublicWidget.Widget.extend({
    selector: ".categories_tile",

    start() {
        let categoriesRow = this.el.querySelector('#categories-row')
         if (categoriesRow) {
             jsonrpc('/categories',{
            }).then(data => {
                let html = ``
                 data.forEach(category=>{
                     if (category.image_512) {
                      html += ` <div class="col-lg-3 s_col_no_bgcolor pt16 pb16">
                                    <div class="card text-bg-white">
                                        <a href="/shop/category/${category.id}">
                                            <h5 class="card-header tit o_default_snippet_text">${category.name}</h5>
                                            <img class="card-img-top" src="data:image/*;base64,${category.image_512}"
                                                alt="" style="width: auto; height: 165px;"/>
                                             <div class="card-footer">
                                                <p class="card-text cat">${category.brand}</p>
                                            </div>
                                        </a>
                                    </div>
                                </div>`
                     } else {
                          html += ` <div class="col-lg-3 s_col_no_bgcolor pt16 pb16">
                                    <div class="card text-bg-white">
                                        <a href="/shop/category/${category.id}">
                                            <h5 class="card-header tit o_default_snippet_text">${category.name}</h5>
                                            <img class="card-img-top" src="/theme_maz/static/src/img/no.jpg"
                                                alt="" style="width: auto; height: 165px;"/>
                                             <div class="card-footer">
                                                <p class="card-text cat">${category.brand}</p>
                                            </div>
                                        </a>
                                    </div>
                                </div>`
                     }
                 })
                categoriesRow.innerHTML = html
            })
         }

    }

})
PublicWidget.registry.MazCategories = MazCategories;
