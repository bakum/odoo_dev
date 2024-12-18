odoo.define('ug_wholesale_shop.wholesale_calculator', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.WholesaleCalculator = publicWidget.Widget.extend({
        selector: '.oe_website_sale.oe_wholesale_calculator',

        start: function () {
            this.calculate()
        },

        _loadData: function() {
            this.packages = []
            var $palette = $('#palette-data');
            this.palette_width = parseInt($palette.data('pl_width') || 0)
            this.palette_height = parseInt($palette.data('pl_height') || 0)
            this.palette_depth = parseInt($palette.data('pl_depth') || 0)
            var $packages = $('.package-data')
            var self = this
            $packages.each(function () {
                var $el = $(this);
                let dt = {}
                dt.width = parseInt($el.data('width') || 0)
                dt.height = parseInt($el.data('height') || 0)
                dt.depth = parseInt($el.data('depth') || 0)
                dt.id = parseInt($el.data('id') || 0)
                dt.quantity = parseFloat($el.text() || 0)
                // console.log('asasas', dt)
                self.packages.push(dt)
            })
        },

        _initCalc: function () {
            for (let i = 0; i < this.packages.length; i++) {
                let dt = this.packages[i]
                dt.pallet11 = dt.width === 0 ? 0 : Math.floor(this.palette_width / dt.width)
                dt.pallet22 = dt.height === 0 ? 0 : Math.floor(this.palette_height / dt.height)
                dt.boxes_on_layer = dt.pallet11 * dt.pallet22

                dt.pallet21 = dt.width === 0 ? 0 : Math.floor(this.palette_height / dt.width)
                dt.pallet12 = dt.height === 0 ? 0 : Math.floor(this.palette_width / dt.height)
                dt.boxes_on_layer2 = dt.pallet21 * dt.pallet12

                dt.max_boxes_on_layer = Math.max(dt.boxes_on_layer, dt.boxes_on_layer2)
                dt.max_layers = dt.depth === 0 ? 0 : Math.floor(this.palette_depth/dt.depth)
            }
            console.log('packages', this.packages)
        },

        calculate: function() {
            this._loadData()
            this._initCalc()
        }
    })
})