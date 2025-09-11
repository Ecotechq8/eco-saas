/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.EmpPortalResignation = publicWidget.Widget.extend({
    selector: '.new_op_form',
    events: {
        'click .new_op_confirm': '_onNewOpConfirm',
        'click .close': '_onCloseClick',
        'change .type_id': '_onOperationTypeChange',
    },

    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
        Date.prototype.toDateInputValue = (function() {
            var local = new Date(this);
            local.setMinutes(this.getMinutes() - this.getTimezoneOffset());
            return local.toJSON().slice(0,10);
        });

        $('#datePicker').val(new Date().toDateInputValue());
    },
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {jQuery} $btn
     * @param {function} callback
     * @returns {Promise}
     */
    _buttonExec: function ($btn, callback) {
        // TODO remove once the automatic system which does this lands in master
        $btn.prop('disabled', true);
        return callback.call(this).guardedCatch(function () {
            $btn.prop('disabled', false);
        });
    },

    _onCloseClick: function () {
        this.destroy();
    },

    _onOperationTypeChange: function (ev) {
        var $select = $(ev.currentTarget);  // Get the selected option element
        var selectedType = $select.find('option:selected').data('type');  // Get the data-type of the selected option
        var $passportFields = $('.passport_withd_div');
        var $proccedWorkFields = $('.procced_work_div')
        var $proccedWorkProccedFields = $('.procced_work_leave_div')
        var $investigationCall = $('.investigation_call_div')
        var $finalReleaseDiv = $('.final_release_div')


        if (selectedType === "final_release"){
            $finalReleaseDiv.show(); 
            $finalReleaseDiv.find('input').attr('required', true);  
        } else {
            $finalReleaseDiv.hide();  
            $finalReleaseDiv.find('input').removeAttr('required');  
        }        

        if (selectedType === 'passport_withdrawal') {
            $passportFields.show();  
            $passportFields.find('input').attr('required', true);  
        } else {
            $passportFields.hide();  
            $passportFields.find('input').removeAttr('required'); 
        }

        if(selectedType === "proceed_work"){
            $proccedWorkFields.show();  
            $proccedWorkFields.find('input').attr('required', true);  
        } else {
            $proccedWorkFields.hide();  
            $proccedWorkFields.find('input').removeAttr('required'); 
        }

        if (selectedType === "proceed_work_leave"){

            $proccedWorkProccedFields.show();  
            $proccedWorkProccedFields.find('input').attr('required', true);  
        } else {
            $proccedWorkProccedFields.hide();  
            $proccedWorkProccedFields.find('input').removeAttr('required'); 
        }

        if (selectedType === "investigation_call"){
            $investigationCall.show(); 
            $investigationCall.find('input').attr('required', true);  
        } else {
            $investigationCall.hide();  
            $investigationCall.find('input').removeAttr('required');  
        }        
    },

    /**
     * @private
     * @returns {Promise}
     */
    _createOp: function () {
        console.log('cccccccccccccccccc');
        var CreationData = {
            employee_id: $('.new_op_form .employee_id').val(),
            date: $('.new_op_form .date_from').val(),
            type_id: $('.new_op_form .type_id').val(),
        }

        var selectedType = $('.new_op_form .type_id option:selected').data('type');
        console.log("selectedType")
        console.log(selectedType)
        if (selectedType === 'passport_withdrawal') {
            CreationData.passport_delivery_date = $('.passport_delivery_date').val();
            CreationData.passport_receive_date = $('.passport_receive_date').val();
            CreationData.purpose_of_passport_withdrawal = $('.purpose_of_passport_withdrawal').val();
        }
        
        if (selectedType === 'proceed_work') {
            CreationData.to_mr_miss = $('.to_mr_miss').val();
        }
    
        if (selectedType === 'final_release') {
            CreationData.last_work_date = $('.last_work_date').val();
        }
    
        if (selectedType === 'proceed_work_leave') {
            CreationData.date_resumes_duty = $('.date_resumes_duty').val();
            CreationData.reason_change_resume_date = $('.reason_change_resume_date').val();
        }
    
        if (selectedType === 'investigation_call') {
            CreationData.calling_date = $('.calling_date').val();
            CreationData.calling_time = $('.calling_time').val();
        }

    	return this.orm.call(
            'hr.operation',
            'create_opFrom_portal',
            [CreationData],

        ).then(function (response) {
            console.log("response")
            console.log(response)
            if (response.errors) {
                console.log('pppppppppppppppppppppppp');
                $('#new-opp-dialog .alert').remove();
                $('#new-opp-dialog div:first').prepend('<div class="alert alert-danger">' + response.errors + '</div>');
                // return Promise.reject(response);
            } else {
                console.log('xxxxxxxxxxxxxxx');
                window.location = '/my/operation/' + response.id;
            }
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {Event} ev
     */
    _onNewOpConfirm: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this._createOp()
        // this._buttonExec($(ev.currentTarget), this._createOp);
    },
    _parse_date: function (value) {
        console.log(value);
        // var date = moment(value, "YYYY-MM-DD", true);
        const date = this.ProcessDate(value);
        if (date) {
            // return date.toDate();
            return this.formatDateToString(date);
        }
        else {
            return false;
        }
    },
});
