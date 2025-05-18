odoo.define('ad_smart_admin.script', ['web.core', 'web.Widget'], function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');

    var YourWidget = Widget.extend({
        template: 'YourTemplate',

        start: function () {
            console.log("Your JavaScript is working!");
        },
    });

    core.action_registry.add('your_widget', YourWidget);

    return {
        YourWidget: YourWidget,
    };
});