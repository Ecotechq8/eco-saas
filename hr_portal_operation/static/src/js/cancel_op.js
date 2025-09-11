/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

    publicWidget.registry.CreateTimesheetPopup = publicWidget.Widget.extend({
        selector: '.create_cancel', // Make sure this matches the container for your widget
        events: {
            'click a': '_onCacnelButtonClick',
            'submit form': '_onFormSubmit',
            'click .closeCustom':'_close_Modal'
        },

        init() {
            this._super(...arguments);
            this.orm = this.bindService("orm");
            },
    
        /**
         * Handles the task button click to show the modal.
         */
        _close_Modal:function(event){
            const $btn = $(event.currentTarget);
            const $modal = $btn.closest('.create_cancel').find('.opModal');
            $modal.modal('toggle'); 
            // $modal.find('#cancelpopup').addClass('show').css('display', 'none')
        },
        _onCacnelButtonClick: function (event) {
            event.preventDefault();
            const $btn = $(event.currentTarget);
            const opId = $btn.data('op-id');
            const $modal = $btn.closest('.create_cancel').find('.opModal');

            $modal.modal('toggle'); 
            $modal.find('#cancelpopup').addClass('show').css('display', 'block')
        },
        /**
         * Handles form submission for creating a timesheet.
         */
        _onFormSubmit: async function (event) {
            event.preventDefault();
            const $form = $(event.currentTarget);
            const opId = $form.data('op-id');
            const name = $form.find('.name').val();

            return this.orm.call(
                'hr.operation',
                'cancel_operation',
                [{
                    op_id: opId,
                    name: name,
                }],
    
            ).then(function (response) {
                if (response.errors) {
                    console.log('pppppppppppppppppppppppp');
                    $('#new-opp-dialog .alert').remove();
                    $('#new-opp-dialog div:first').prepend('<div class="alert alert-danger">' + response.errors + '</div>');
                    return Promise.reject(response);
                } else {
                    console.log('xxxxxxxxxxxxxxx');
                    window.location = '/my/operation/' + response.id;
                }
            });

        },
    });
