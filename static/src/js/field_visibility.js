// odoo.define('ad_smart_admin.field_visibility', function (require) {
//     "use strict";

//     var viewRegistry = require('web.view_registry');
//     var rpc = require('web.rpc');

//     var ListView = viewRegistry.get('list');

//     ListView.include({
//         willStart: function () {
//             var self = this;
//             return this._super().then(function () {
//                 return rpc.query({
//                     route: '/ad_smart_admin/get_fields_visibility',
//                 }).then(function (result) {
//                     self.fieldsVisibility = result;
//                 });
//             });
//         },

//         renderButtons: function ($node) {
//             this._super.apply(this, arguments);
//             var self = this;
//             var fieldsVisibility = this.fieldsVisibility;

//             if (fieldsVisibility) {
//                 this.$el.find('th').each(function (index, th) {
//                     var fieldName = $(th).data('name');
//                     var field = fieldsVisibility.find(f => f.name === fieldName);
//                     if (field && field.hide) {
//                         $(th).hide();
//                         self.$el.find('td[data-field="' + fieldName + '"]').hide();
//                     }
//                 });
//             }
//         }
//     });
// });
