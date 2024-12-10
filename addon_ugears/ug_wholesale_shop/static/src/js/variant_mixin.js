odoo.define('ug_wholesale_shop.VariantMixin', function (require) {
    'use strict';

    var VariantMixin = require('sale.VariantMixin');

    // const originalOnClickAddCartJSON = VariantMixin.onClickAddCartJSON;
    VariantMixin.onClickAddCartJSON = function (ev) {
        // originalOnClickAddCartJSON.apply(this, [ev]);
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        var $input = $link.closest('.input-group').find("input");
        var min = parseFloat($input.data("min") || 0);
        var max = parseFloat($input.data("max") || Infinity);
        var qty_in_cartoon = parseInt($input.data("qty-in-cartoon") || 1);
        var previousQty = parseFloat($input.val() || 0, 10);
        var quantity = ($link.has(".fa-minus").length ? -qty_in_cartoon : qty_in_cartoon) + previousQty;
        var newQty = quantity > min ? (quantity < max ? quantity : max) : min;

        if (newQty !== previousQty) {
            $input.val(newQty).trigger('change');
        }
        return false;
    }

return VariantMixin;

});