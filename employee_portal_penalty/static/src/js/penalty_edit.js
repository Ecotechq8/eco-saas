/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { loadJS } from "@web/core/assets";

publicWidget.registry.EmpPenaltyPortal = publicWidget.Widget.extend({
    selector: '#wrapwrap:has(.edit_penalty_form)',
    events: {
        'click .edit_penalty_confirm': '_onEditPenaltyConfirm',
    },
    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
        // this.dialog = this.bindService("dialog");
    },


    _buttonExec: function ($btn, callback) {
        // TODO remove once the automatic system which does this lands in master
        $btn.prop('disabled', true);
        return callback.call(this).guardedCatch(function () {
            $btn.prop('disabled', false);
        });
    },

    _editPenaltyRequest: function () {
        return this.orm.call(
             'penalty.request',
            'update_penalty_portal',
            [[parseInt($('.edit_penalty_form .penalty_id').val())], {
            	PenaltyID: parseInt($('.edit_penalty_form .penalty_id').val()),
                emp_manager_opinion: $('.edit_penalty_form .emp_manager_opinion').val(),
                emp_manager_feedback: $('.edit_penalty_form .emp_manager_feedback').val(),
                employee_cause_of_penalty: $('.edit_penalty_form .employee_cause_of_penalty').val(),
                employee_approve_of_cause: $('.edit_penalty_form .employee_approve_of_cause').val(),
                employee_other_approve: $('.edit_penalty_form .employee_other_approve').val(),
                hr_manager_feedback: $('.edit_penalty_form .hr_manager_feedback').val(),
            }],
        ).then(function () {
            window.location.replace('/my/penalties');
//            .reload();
        });
    },

    _onEditPenaltyConfirm: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this._editPenaltyRequest()
//         this._buttonExec($(ev.currentTarget), this._editPenaltyRequest);
    },


});
// });
