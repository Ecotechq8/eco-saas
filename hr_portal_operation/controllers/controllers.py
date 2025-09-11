# See LICENSE file for full copyright and licensing details

from collections import OrderedDict
from operator import itemgetter
from odoo import fields
from odoo import http
from odoo.http import request
from odoo.tools import date_utils, groupby as groupbyelem
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.tools.translate import _


class WebsiteAccount(CustomerPortal):

    def get_domain_my_operation(self, user):
        emp = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        return [('employee_id', '=', emp and emp.id or False), ('type_id.is_portal', '=', True)]

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'op_count' in counters:
            emp = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
            op_count = request.env['hr.operation'].sudo().search_count([('employee_id', '=', emp.id)])
            values['op_count'] = op_count
        return values

    @http.route(['/my/operation', '/my/operation/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_operation(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, groupby='none',
                            **kw):
        values = self._prepare_portal_layout_values()
        HrOp = request.env['hr.operation']
        operation_sudo = request.env['hr.operation'].sudo()
        domain = self.get_domain_my_operation(request.env.user)

        user = request.env.user

        # fileter  By
        searchbar_filters = {
            'draft': {'label': _('Draft'), 'domain': [('state', '=', 'draft')]},
            'confirmed': {'label': _('confirmed'), 'domain': [('state', '=', 'confirmed')]},
            'cancelled': {'label': _('Canceled'), 'domain': [('state', '=', 'cancelled')]},

        }
        # sort By
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
        }
        # group By
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'op': {'input': 'ops', 'label': _('Op State')},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        # default filter by value
        if not filterby:
            filterby = 'confirmed'
        domain += searchbar_filters[filterby]['domain']
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        # pager
        op_count = HrOp.search_count(domain)
        pager = request.website.pager(
            url="/my/operation",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=op_count,
            page=page,
            step=self._items_per_page
        )
        # default groupby
        if groupby == 'ops':
            order = "employee_id, %s" % order
        # content according to pager and archive selected
        operation = HrOp.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        if groupby == 'none':
            grouped_op = []
            if operation:
                grouped_op = [operation]
        else:
            grouped_op = [operation_sudo.concat(*g) for k, g in groupbyelem(operation, itemgetter('employee_id'))]

        emp = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        values.update({
            'date': date_begin,
            'operation': operation,
            'grouped_op': grouped_op,
            'page_name': 'operation',
            'emp_id': emp and emp.id or False,
            'emp_name': emp and emp.name or False,
            'default_url': '/my/operation',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'searchbar_groupby': searchbar_groupby,
            'sortby': sortby,
            'groupby': groupby,
            'filterby': filterby,
        })
        return request.render("hr_portal_operation.portal_my_op_details", values)

    @http.route(['''/my/operation/<model('hr.operation'):operation>'''], type='http', auth="user",
                website=True)
    def portal_my_operation_op(self, operation, **kw):
        user = request.env.user
        emp = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        return request.render(
            "hr_portal_operation.portal_my_op_edit", {
                'operation': operation,
                'emp_id': emp and emp.id or False,
                'current_emp': request.env.user.employee_id.name
            })

    @http.route(['/my/operation/request'], type='http', auth="user", website=True)
    def operation_new_request(self):
        user = request.env.user
        emp = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        operation_types = request.env['hr.operation.type'].sudo().search([('is_portal', '=', True)])
        return request.render(
            "hr_portal_operation.new_operation_request", {
                'emp_id': emp.id or False,
                'emp_name': emp.name or False,
                'operation_types': operation_types
            })
