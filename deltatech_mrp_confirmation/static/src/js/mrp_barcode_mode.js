odoo.define('deltatech_mrp_confirmation.mrp_barcode_mode', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
var Widget = require('web.Widget');
var Session = require('web.session');
var BarcodeHandlerMixin = require('barcodes.BarcodeHandlerMixin');

var QWeb = core.qweb;
var _t = core._t;


var MrpBarcodeMode = Widget.extend(BarcodeHandlerMixin, {

    events: {
        "click .o_mrp_confirmation_barcode_button_search": function() {
        var modal = $('#barcodeModal');
        this.barcode = modal.find('.modal-body input').val();
        modal.modal('hide');
        return this.on_barcode_scanned(this.barcode);
        },
    },

    init: function (parent, action) {
        // Note: BarcodeHandlerMixin.init calls this._super.init, so there's no need to do it here.
        // Yet, "_super" must be present in a function for the class mechanism to replace it with the actual parent method.
        this._super;
        var self = this;
        this.barcode = '';
        this.conf_wizard = new Model('mrp.production.conf');
        this.conf_wizard.call("create",[{}]).then(function(id) {
            self.conf_wizard_id = id;
        });

        BarcodeHandlerMixin.init.apply(this, arguments);
    },

    start: function () {
        var self = this;
        self.session = Session;
        var res_company = new Model('res.company');
        res_company.query(['name'])
           .filter([['id', '=', self.session.company_id]])
           .all()
           .then(function (companies){
                self.company_name = companies[0].name;
                self.company_image_url = self.session.url('/web/image', {model: 'res.company', id: self.session.company_id, field: 'logo',})
                self.$el.html(QWeb.render("MrpConfirmationBarcodeMode", {widget: self}));

            });
        return self._super.apply(this, arguments);
    },

    display_data: function(){
        var self = this;
        self.session = Session;
        var conf_wizard = new Model('mrp.production.conf');
        conf_wizard.query()  //['production_id','worker_id','operation_id','code']
            .filter([['id', '=', self.conf_wizard_id]])
           .all()
           .then(function (conf){
                self.$(".o_mrp_confirmation_barcode_item").html(QWeb.render("MrpConfirmationBarcodeItem", {conf: conf[0]}));
           });

    },

    on_barcode_scanned: function(barcode) {
        var self = this;
        self.conf_wizard.call("search_scanned",  [self.conf_wizard_id, barcode] )
            .then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(_('Warning'),result.warning.message);

                }
                self.display_data();
            });

    }
});

core.action_registry.add('mrp_confirmation_barcode_mode', MrpBarcodeMode);

return MrpBarcodeMode;

});