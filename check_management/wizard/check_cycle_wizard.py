from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError


class check_cycle_accs(models.TransientModel):
    _name = 'check.cycle.accounts.default'

    @api.model
    def get_check_lines(self):
        checks = self.env['check.management'].search(
            [('id', 'in', self.env.context['active_ids'])])
        app_checks = []
        for ch in reversed(checks):
            val = {}
            val['check_number'] = ch.check_number
            val['check_id'] = ch.id
            val['check_amt'] = ch.amount
            val['paid_amt'] = ch.open_amount
            val['open_amt'] = ch.open_amount
            line = self.env['appove.check.lines'].create(val)
            # app_checks.append((0,0, val))
            app_checks.append(line.id)
        return app_checks

    name = fields.Char(default="Please choose the bank Account", readonly=True)
    name_cancel = fields.Char(
        default="Are you sure you want to cancel the checks", readonly=True)
    name_reject = fields.Char(
        default="Are you sure you want to reject the checks", readonly=True)
    name_return = fields.Char(
        default="Are you sure you want to return the checks to company", readonly=True)
    name_approve = fields.Char(default="Please choose the bank Account", readonly=True)
    name_debit = fields.Char(default="Please choose the bank Account", readonly=True)
    name_csreturn = fields.Char(
        default="Are you sure you want to return the checks to customer", readonly=True)
    name_vendor_return = fields.Char(
        default="Are you sure you want to return the checks to Vendor", readonly=True)

    name_split_merge = fields.Char(default="Please create the new checks", readonly=True)
    account_id = fields.Many2one('account.account', string="Account")
    # journal_domain = fields.Char(compute="_compute_journal_domain", store=False)
    journal_domain_ids = fields.Many2many("account.journal", store=False)


    @api.depends_context('action_wiz', 'active_ids')
    @api.onchange('name')
    def _compute_journal_domain(self):
        for record in self:
            action_wiz = self._context.get("action_wiz")
            if action_wiz == "deposit":
                # Filter journals with deposit_check=True
                record.journal_domain_ids = [[6,0,self.env['account.journal'].search([('deposit_check', '=', True)]).ids]]

                


            elif action_wiz == "approve":
                # Filter journals based on the bank_ids in checks
                record.journal_domain_ids = [[6,0,self.env['account.journal'].search([('bank_id', 'in', self.env['check.management'].browse(self._context.get('active_ids', [])).mapped("dep_bank").ids)]).ids]]

            else:
                # No filter if no specific context
                record.journal_domain_ids = [[5]]

    journal_id = fields.Many2one('account.journal', string="Journal")
    reject_reason = fields.Text(string="Rejection reason")
    approve_check = fields.Many2many(
        'appove.check.lines', ondelete="cascade", default=get_check_lines)
    total_amt_checks = fields.Float(
        string="total Amount of Checks", compute="getcheckstotamt")
    merge_split_checks = fields.Many2many('split.merge.check', ondelete="cascade")
    merge_split_ids = fields.One2many('split.merge.check', 'split_merge_parent_id')
    investor_spilt = fields.Many2one('res.partner', string=_("Partner"))
    payment_date = fields.Date(required=True)
    transaction_date = fields.Date(default=fields.Date.context_today, readonly=True)
    dep_bank_id = fields.Many2one("res.bank",string="Deposit Bank")

    @api.onchange('name')
    def calc_default_journals(self):
        if self._context.get("action_wiz")=="depoist":
            journal_id = self.env['account.journal'].search([('deposit_check','=',True)])
            if journal_id:
                self.journal_id = journal_id.id

        if self._context.get("action_wiz")=="approve":
            check_bank = list(set(self.env['check.management'].browse(self.env.context['active_ids']).mapped("dep_bank").ids))
            if len(check_bank)==1:
                journal_id = self.env['account.journal'].search([('bank_id','in',check_bank)])
                if journal_id:
                    self.journal_id = journal_id.id


    @api.depends('name_split_merge')
    def getcheckstotamt(self):
        # check same customer
        checks = self.env['check.management'].search(
            [('id', 'in', self.env.context['active_ids'])])
        if any(inv.investor_id != checks[0].investor_id for inv in checks):
            raise exceptions.ValidationError(
                _("u cant split checks for different customers ."))

        for rec in self:
            rec.total_amt_checks = 0
            checks = rec.env['check.management'].search(
                [('id', 'in', self.env.context['active_ids'])])
            for ch in checks:
                rec.total_amt_checks += ch.open_amount
                rec.investor_spilt = ch.investor_id.id

    # @api.multi
    def action_save(self):
        if 'action_wiz' in self.env.context:
            if self.env.context['action_wiz'] == 'depoist':
                if not self.journal_id:
                    raise exceptions.ValidationError(_('Please provide the bank account'))
                checks = self.env['check.management'].search(
                    [('id', 'in', self.env.context['active_ids'])])
                for check in checks:
                    check.payment_date = self.payment_date
                    check.transaction_date = self.transaction_date
                    check.dep_bank = self.dep_bank_id.id

                    move = {
                        'date': self.payment_date,
                        'name': 'Depoisting Check number ' + check.check_number,
                        'journal_id': self.journal_id.id,
                        'ref': 'Depoisting Check number ' + check.check_number,
                        'company_id': self.env.user.company_id.id,
                        'check_id':check.id,
                        'check_payment_state':'depoisted'

                    }

                    move_line = {
                        'name': 'Depoisting Check number ' + check.check_number,
                        'partner_id': check.investor_id.id,
                        'ref': 'Depoisting Check number ' + check.check_number,
                        'check_id':check.id,
                        'check_payment_state':'depoisted'
                    }

                    debit_account = []
                    credit_account = []
                    debit_account.append(
                        {'account': self.journal_id.default_account_id.id, 'percentage': 100})
                    if check.notes_rece_id:
                        credit_account.append(
                            {'account': check.notes_rece_id.id, 'percentage': 100})
                    else:
                        credit_account.append(
                            {'account': check.unit_id.project_id.NotesReceivableAccount.id, 'percentage': 100})
                    self.sudo().env['create.moves'].create_move_lines(move=move, move_line=move_line,
                                                                      debit_account=debit_account,
                                                                      credit_account=credit_account,
                                                                      src_currency=checks[0].currency_id,
                                                                      amount=check.open_amount)
                    check.state = 'depoisted'
                    check.under_collect_id = self.journal_id.default_account_id.id
                    check.under_collect_jour = self.journal_id.id
            elif self.env.context['action_wiz'] == 'approve':
                if len(set(self.env['check.management'].search([
                    ('id', 'in', self.env.context['active_ids'])
                ]).mapped("dep_bank"))) > 1:
                    raise exceptions.ValidationError(_('Cannot approve mutli bank account'))


                if not self.journal_id:
                    raise exceptions.ValidationError(_('Please provide the bank account'))
                for approve_ch_line in self.approve_check:
                    z = ""
                    for x in self.approve_check:
                        z = z + (str(x.open_amt)) + ","
                    if approve_ch_line.open_amt < approve_ch_line.paid_amt:
                        raise exceptions.ValidationError(
                            _('The paid amount is greater than open amount for some checks\n' + z))
                checks = self.env['check.management'].search(
                    [('id', 'in', self.env.context['active_ids'])])
                for check in checks:
                    # 'date':check.payment_date,
                    check.payment_date = self.payment_date
                    check.transaction_date = self.transaction_date
                    debit_account = []
                    credit_account = []
                    move = {
                        'date': self.payment_date,
                        'name': 'Approving Check number ' + check.check_number,
                        'journal_id': self.journal_id.id,
                        'ref': 'Approving Check number ' + check.check_number,
                        'company_id': self.env.user.company_id.id,    
                        'check_id':check.id,
                        'check_payment_state':'approved'

                    }
                    move_line = {
                        'name': 'Approving Check number ' + check.check_number,
                        'partner_id': check.investor_id.id,
                        'ref': 'Approving Check number ' + check.check_number,
                        'check_id':check.id,
                        'check_payment_state':'approved'
                    }
                    checkamt = check.amount
                    for approve_ch_line in self.approve_check:
                        if approve_ch_line.check_id == check.id:
                            checkamt = approve_ch_line.paid_amt
                            check.open_amount -= approve_ch_line.paid_amt
                    if check.investor_id:
                        debit_account.append(
                            {'account': self.journal_id.default_account_id.id, 'percentage': 100})

                        if check.state != 'returned':
                            if check.under_collect_id:
                                credit_account.append(
                                    {'account': check.under_collect_id.id, 'percentage': 100})
                            else:
                                if check.notes_rece_id:
                                    credit_account.append({'account': check.notes_rece_id.id, 'percentage': 100})
                        else:
                            credit_account.append(
                                {'account': check.notes_rece_id.id, 'percentage': 100})

                            # else:
                            #     credit_account.append(
                            #         {'account': check.unit_id.project_id.NotesReceivableAccount.id, 'percentage': 100})

                    if checkamt > 0.0:
                        self.sudo().env['create.moves'].create_move_lines(move=move, move_line=move_line,
                                                                          debit_account=debit_account,
                                                                          credit_account=credit_account,
                                                                          src_currency=checks[0].currency_id,
                                                                          amount=checkamt)
                    if check.open_amount == 0.0:
                        check.state = 'approved'
            elif self.env.context['action_wiz'] == 'reject':
                checks = self.env['check.management'].search(
                    [('id', 'in', self.env.context['active_ids'])])
                for check in checks:
                    check.payment_date = self.payment_date
                    check.transaction_date = self.transaction_date
                    check.state = 'rejected'
                    check.reject_reason = self.reject_reason
                    message = "Rejection Reason is " + str(self.reject_reason)
                    check.message_post(body=message)
            elif self.env.context['action_wiz'] == 'return':
                checks = self.env['check.management'].search(
                    [('id', 'in', self.env.context['active_ids'])])
                for check in checks:
                    check.payment_date = self.payment_date
                    check.transaction_date = self.transaction_date

                    move = {
                        'date': self.payment_date,
                        'name': 'Returning Check number ' + check.check_number,
                        'journal_id': check.under_collect_jour.id,
                        'ref': 'Returning Check number ' + check.check_number,
                        'company_id': self.env.user.company_id.id,
                        'check_id':check.id,
                        'check_payment_state':'returned'

                    }

                    move_line = {
                        'name': 'Returning Check number ' + check.check_number,
                        'partner_id': check.investor_id.id,  # check.partner_id.id or
                        'ref': 'Returning Check number ' + check.check_number,
                        'check_id':check.id,
                        'check_payment_state':'returned'
                    }
                    debit_account = []
                    credit_account = []
                    credit_account.append(
                        {'account': check.under_collect_jour.default_account_id.id, 'percentage': 100})
                    if check.notes_rece_id:
                        debit_account.append(
                            {'account': check.notes_rece_id.id, 'percentage': 100})
                    else:
                        debit_account.append(
                            {'account': check.unit_id.project_id.NotesReceivableAccount.id, 'percentage': 100})
                    self.sudo().env['create.moves'].create_move_lines(move=move, move_line=move_line,
                                                                      debit_account=debit_account,
                                                                      credit_account=credit_account,
                                                                      src_currency=checks[0].currency_id,
                                                                      amount=check.open_amount)
                    check.state = 'returned'
            elif self.env.context['action_wiz'] == 'debit':
                if not self.journal_id:
                    raise exceptions.ValidationError(_('Please provide the bank account'))
                for approve_ch_line in self.approve_check:
                    z = ""
                    for x in self.approve_check:
                        z = z + (str(x.open_amt)) + ","
                    if approve_ch_line.open_amt < approve_ch_line.paid_amt:
                        raise exceptions.ValidationError(
                            _('The paid amount is greater than open amount for some checks\n' + z))
                checks = self.env['check.management'].search(
                    [('id', 'in', self.env.context['active_ids'])])
                for check in checks:
                    check.payment_date = self.payment_date
                    check.transaction_date = self.transaction_date

                    debit_account = []
                    credit_account = []
                    move = {
                        'date': self.payment_date,
                        'name': 'Debiting Check number ' + check.check_number,
                        'journal_id': self.journal_id.id,
                        'ref': 'Debiting Check number ' + check.check_number,
                        'company_id': self.env.user.company_id.id,
                        'check_id':check.id,
                        'check_payment_state':'debited'
                    }
                    move_line = {
                        'name': 'Debiting Check number ' + check.check_number,
                        'partner_id': check.investor_id.id,
                        'ref': 'Debiting Check number ' + check.check_number,
                        'check_id':check.id,
                        'check_payment_state':'debited'
                    }
                    checkamt = check.amount
                    for approve_ch_line in self.approve_check:
                        if approve_ch_line.check_id == check.id:
                            checkamt = approve_ch_line.paid_amt
                            check.open_amount -= approve_ch_line.paid_amt
                    if check.investor_id:
                        debit_account.append(
                            {'account': self.journal_id.default_account_id.id, 'percentage': 100})
                        credit_account.append(
                            {'account': check.notes_rece_id.id, 'percentage': 100})

                    if checkamt > 0.0:
                        self.sudo().env['create.moves'].create_move_lines(move=move, move_line=move_line,
                                                                          debit_account=credit_account,
                                                                          credit_account=debit_account,
                                                                          src_currency=checks[0].currency_id,
                                                                          amount=checkamt)
                    if check.open_amount == 0.0:
                        check.state = 'debited'


            elif self.env.context['action_wiz'] == 'vendor_return':
                checks = self.env['check.management'].search(
                    [('id', 'in', self.env.context['active_ids'])])
                for check in checks:
                    if not check.journal_id:
                        err = _('Missing Journal for: {}'.format(check.name))
                        raise UserError(err)

                    check.payment_date = self.payment_date
                    check.transaction_date = self.transaction_date
                    move = {
                        'date': self.payment_date,
                        'name': 'Returning Check number ' + check.check_number + ' to Vendor',
                        'journal_id': check.journal_id.id,
                        'ref': 'Returning Check number ' + check.check_number + ' to Vendor',
                        'company_id': self.env.user.company_id.id,
                        'check_id':check.id,
                        'check_payment_state':'vendor_return'
                    }
                    move_line = {
                        'name': 'Returning Check number ' + check.check_number + ' to Vendor',
                        'partner_id': check.investor_id.id,
                        'ref': 'Returning Check number ' + check.check_number + ' to Vendor',
                        'check_id':check.id,
                        'check_payment_state':'vendor_return'
                    }

                    if check.investor_id:
                        debit_account = [
                            # check.investor_id.property_account_receivable_id.id
                            {'account': check.notespayable_id.id, 'percentage': 100}]
                        credit_account = [
                            # check.investor_id.property_account_receivable_id.id
                            {'account': check.investor_id.property_account_payable_id.id, 'percentage': 100}]
                        self.env['create.moves'].create_move_lines(move=move, move_line=move_line,
                                                                   debit_account=debit_account,
                                                                   credit_account=credit_account,
                                                                   src_currency=checks[0].currency_id,
                                                                   amount=check.amount)
                    check.state = 'vendor_return'
                    check.check_state = 'suspended'

            elif self.env.context['action_wiz'] == 'cs_return':
                checks = self.env['check.management'].search(
                    [('id', 'in', self.env.context['active_ids'])])
                for check in checks:
                    check.payment_date = self.payment_date
                    check.transaction_date = self.transaction_date

                    if not check.journal_id:
                        err = _('Missing Journal for: {}'.format(check.name))
                        raise UserError(err)
                    move = {
                        'date': self.payment_date,
                        'name': 'Returning Check number ' + check.check_number + ' to customer',
                        'journal_id': check.journal_id.id,
                        'ref': 'Returning Check number ' + check.check_number + ' to customer',
                        'company_id': self.env.user.company_id.id,
                        'check_id':check.id,
                        'check_payment_state':'cs_return'

                    }
                    move_line = {
                        'name': 'Returning Check number ' + check.check_number + ' to customer',
                        'partner_id': check.investor_id.id,
                        'ref': 'Returning Check number ' + check.check_number + ' to customer',
                        'check_id':check.id,
                        'check_payment_state':'cs_return'
                    }

                    if check.investor_id:
                        debit_account = [
                            {'account': check.investor_id.property_account_receivable_id.id, 'percentage': 100}]
                        credit_account = [
                            {'account': check.notespayable_id.id, 'percentage': 100}]
                        self.env['create.moves'].create_move_lines(move=move, move_line=move_line,
                                                                   debit_account=debit_account,
                                                                   credit_account=credit_account,
                                                                   src_currency=checks[0].currency_id,
                                                                   amount=check.amount)

                    check.state = 'cs_return'
                    check.check_state = 'suspended'
            elif self.env.context['action_wiz'] == 'split_merge':
                checks = self.env['check.management'].search(
                    [('id', 'in', self.env.context['active_ids'])])
                # check same customer
                if any(inv.investor_id != checks[0].investor_id for inv in checks):
                    raise exceptions.ValidationError(
                        _("u cant split checks for different customers ."))
                # check same customer
                if any(inv.currency_id != checks[0].currency_id for inv in checks):
                    raise exceptions.ValidationError(
                        _("u cant split checks for different Currencies ."))
                for x in checks:
                    if not x.notes_rece_id:
                        raise exceptions.ValidationError(
                            _('Action not allowed on normal checks'))

                new_tot_amt = 0
                notes_rece_id = 0
                ch_state = 'holding'
                ch_patner = x.investor_id.id
                if checks[0]:

                    notes_rece_id = checks[0].notes_rece_id.id
                    ch_state = checks[0].state
                else:
                    raise exceptions.ValidationError(
                        _('Action not allowed on normal checks'))
                for ch in checks:
                    if notes_rece_id != ch.notes_rece_id.id:
                        raise exceptions.ValidationError(
                            _('You can not merge checks from different journals'))
                for sp_mr_checks in self.merge_split_ids:
                    new_tot_amt += sp_mr_checks.amount
                if new_tot_amt != self.total_amt_checks:
                    raise exceptions.ValidationError(
                        _('Amount of new Checks is not equal to amount of selected checks'))

                for sp_mr_checks in self.merge_split_ids:
                    check_line_val = {}
                    check_line_val['check_number'] = sp_mr_checks.check_number
                    check_line_val['check_date'] = sp_mr_checks.check_date
                    check_line_val['check_bank'] = sp_mr_checks.bank.id
                    check_line_val['dep_bank'] = sp_mr_checks.dep_bank.id
                    check_line_val['amount'] = sp_mr_checks.amount
                    check_line_val['open_amount'] = sp_mr_checks.amount
                    check_line_val['amount_reg'] = 0
                    check_line_val['payment_date'] = self.payment_date
                    check_line_val['transaction_date'] = self.transaction_date
                    check_line_val['state'] = ch_state
                    check_line_val['investor_id'] = ch_patner
                    check_line_val['type'] = 'regular'
                    check_line_val['check_type'] = 'rece'
                    check_line_val['currency_id'] = checks[0].currency_id.id
                    check_line_val['notes_rece_id'] = notes_rece_id
                    check_line_val['notespayable_id'] = notes_rece_id
                    check_line_val['journal_id'] = sp_mr_checks.payment_journal.id
                    new_check = self.env['check.management'].create(check_line_val)
                for x in checks:
                    x.unlink()
        else:
            raise exceptions.ValidationError(_('Unknown Action'))
        return True


class approve_check_lines(models.Model):
    _name = 'appove.check.lines'

    check_number = fields.Char()
    check_id = fields.Integer()
    check_amt = fields.Float()
    paid_amt = fields.Float()
    open_amt = fields.Float()


class split_merge_check(models.TransientModel):
    _name = 'split.merge.check'
    _order = 'check_number asc'

    check_number = fields.Char(string=_("Check number"), required=True)
    check_date = fields.Date(string=_('Check Date'), required=True)
    amount = fields.Float(string=_('Amount'), required=True)
    bank = fields.Many2one('res.bank', string=_("Check Bank Name"))
    dep_bank = fields.Many2one('res.bank', string=_("Depoist Bank"))
    payment_journal = fields.Many2one('account.journal', string=_("Payment Journal"), required=True)
    split_merge_parent_id = fields.Many2one("check.cycle.accounts.default")
