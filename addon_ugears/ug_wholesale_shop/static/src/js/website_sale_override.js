odoo.define('ug_wholesale_shop.website_sale_override', function (require) {
    'use strict';

    var core = require('web.core');
    const publicWidget = require('web.public.widget');
    require('website_sale.website_sale');
    var wSaleUtils = require('website_sale.utils');

    //extending
    // publicWidget.registry.WebsiteSaleNew = publicWidget.registry.WebsiteSale.extend({})

    //including
    publicWidget.registry.WebsiteSale.include({
        _changeCartQuantity: function ($input, value, $dom_optional, line_id, productIDs) {
            // this._super.apply(this, arguments);
            _.each($dom_optional, function (elem) {
                $(elem).find('.js_quantity').text(value);
                productIDs.push($(elem).find('span[data-product-id]').data('product-id'));
            });
            $input.data('update_change', true);
            var $palette = $('#palette-data');
            var palette_id = parseInt($palette.data('pl_id') || 0)

            var params = {
                route: "/shop/cart/update_json",
                params: {
                    line_id: line_id,
                    product_id: parseInt($input.data('product-id'), 10),
                    set_qty: value
                },
            }
            if (palette_id > 0 ) params.params.palette_id = palette_id

            this._rpc(params).then(function (data) {
                $input.data('update_change', false);
                var check_value = parseInt($input.val() || 0, 10);
                if (isNaN(check_value)) {
                    check_value = 1;
                }
                if (value !== check_value) {
                    $input.trigger('change');
                    return;
                }
                sessionStorage.setItem('website_sale_cart_quantity', data.cart_quantity);
                if (!data.cart_quantity) {
                    return window.location = '/shop/cart';
                }
                $input.val(data.quantity);
                $('.js_quantity[data-line-id=' + line_id + ']').val(data.quantity).text(data.quantity);

                wSaleUtils.updateCartNavBar(data);
                wSaleUtils.showWarning(data.warning);
                // Propagating the change to the express checkout forms
                core.bus.trigger('cart_amount_changed', data.amount, data.minor_amount);
            });
        },
    })
})