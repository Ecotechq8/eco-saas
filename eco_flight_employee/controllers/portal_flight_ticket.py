from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from collections import OrderedDict


class PortalFlightTicket(CustomerPortal):

    @http.route('/flight_ticket/get_employee_data', type='json', auth='user')
    def get_employee_data(self, employee_id):
        employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        remaining = 0
        contract = employee.contract_id

        if contract:
            total_tickets = contract.ticket_count or 0
            confirmed_requests = request.env['flight.ticket.request'].sudo().search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'confirmed')
            ])
            used = sum(r.number_of_ticket for r in confirmed_requests)
            remaining = total_tickets - used
        else:
            total_tickets = 0

        return {
            'remaining_ticket': remaining,
            'ticket_count': total_tickets,
            'contract_id': contract.id if contract else False
        }

    def _get_flight_ticket_domain(self, user):
        # Get the employee linked to the current user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        return [('employee_id', '=', employee.id)] if employee else [('id', '=', 0)]

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'flight_ticket_count' in counters:
            domain = self._get_flight_ticket_domain(request.env.user)
            values['flight_ticket_count'] = request.env['flight.ticket.request'].sudo().search_count(domain)
        return values

    @http.route(['/my/flight_ticket', '/my/flight_ticket/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_flight_ticket(self, page=1, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        FlightTicket = request.env['flight.ticket.request'].sudo()
        domain = self._get_flight_ticket_domain(request.env.user)

        emp = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
        }

        searchbar_filters = {
            'draft': {'label': _('Draft'), 'domain': [('state', '=', 'draft')]},
            'submitted': {'label': _('Submitted'), 'domain': [('state', '=', 'submit_for_approval')]},
            'approved': {'label': _('Approved'), 'domain': [('state', '=', 'approval')]},
            'confirmed': {'label': _('Confirmed'), 'domain': [('state', '=', 'confirmed')]},
        }

        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        if not filterby:
            filterby = 'draft'
        domain += searchbar_filters[filterby]['domain']

        ticket_count = FlightTicket.search_count(domain)
        pager = request.website.pager(
            url="/my/flight_ticket",
            url_args={'sortby': sortby, 'filterby': filterby},
            total=ticket_count,
            page=page,
            step=self._items_per_page
        )

        tickets = FlightTicket.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'tickets': tickets,
            'page_name': 'flight_ticket',
            'pager': pager,
            'employee': emp,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'sortby': sortby,
            'filterby': filterby,
            'default_url': '/my/flight_ticket',
        })
        return request.render("eco_flight_employee.portal_my_flight_ticket_details", values)

    @http.route(['/my/flight_ticket/new'], type='http', auth="user", website=True)
    def new_flight_ticket_request(self):
        current_employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        remaining_ticket = 0
        contract_id = False

        if current_employee and current_employee.contract_id:
            contract = current_employee.contract_id
            contract_id = contract.id
            total_tickets = contract.ticket_count or 0

            confirmed_requests = request.env['flight.ticket.request'].sudo().search([
                ('employee_id', '=', current_employee.id),
                ('state', '=', 'confirmed')
            ])
            used = sum(r.number_of_ticket for r in confirmed_requests)
            remaining_ticket = total_tickets - used

        return request.render("eco_flight_employee.new_flight_ticket_request", {
            'current_employee': current_employee,
            'remaining_ticket': remaining_ticket,
            'contract_id': contract_id,
        })

    @http.route(['/my/flight_ticket/submit'], type='http', methods=['POST'], auth="user", website=True, csrf=True)
    def submit_flight_ticket_request(self, **post):
        employee_id = post.get('employee_id')
        class_type = post.get('class_type')
        ticket_qty = post.get('number_of_ticket')
        amount = post.get('amount_untaxed')
        contract_id = post.get('contract_id')
        remaining_ticket = post.get('remaining_ticket')

        if not employee_id or not class_type or not ticket_qty or not amount:
            return request.redirect('/my/flight_ticket/new?error=missing_fields')

        if int(ticket_qty) > int(remaining_ticket):
            employee = request.env['hr.employee'].sudo().browse(int(employee_id))
            return request.render("eco_flight_employee.new_flight_ticket_request", {
                'current_employee': employee,
                'remaining_ticket': int(remaining_ticket),
                'contract_id': contract_id,
                'class_type': class_type,
                'number_of_ticket': ticket_qty,
                'amount_untaxed': amount,
                'error': _('Number of tickets requested (%s) exceeds your remaining tickets (%s).') % (
                    ticket_qty, remaining_ticket),
            })

        request.env['flight.ticket.request'].sudo().create({
            'employee_id': int(employee_id),
            'class_type': class_type,
            'number_of_ticket': int(ticket_qty),
            'amount_untaxed': float(amount),
            'contract_id': int(contract_id) if contract_id else False,
        })

        return request.redirect('/my/flight_ticket')
