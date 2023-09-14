##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2023 Comunitea Servicios Tecnológicos S.L. All Rights Reserved
#    Vicente Ángel Gutiérrez <vicente@comunitea.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from collections import OrderedDict
from odoo.http import request


class PortalAccount(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'purchase_request_count' in counters:
            purchase_request_count = request.env['purchase.request'].search_count(self._get_purchase_requests_domain()) \
                if request.env['purchase.request'].check_access_rights('read', raise_exception=False) else 0
            values['purchase_request_count'] = purchase_request_count
        
        # stock.picking
        if 'stock_picking_count' in counters:
            stock_picking_count = request.env['stock.picking'].search_count(self._get_stock_pickings_domain()) \
                if request.env['stock.picking'].check_access_rights('read', raise_exception=False) else 0
            values['stock_picking_count'] = stock_picking_count
        return values

    # ------------------------------------------------------------
    # My purchase requests
    # ------------------------------------------------------------

    def _purchase_request_get_page_view_values(self, purchase_request, access_token, **kwargs):
        values = {
            'page_name': 'purchase_request',
            'purchase_request': purchase_request,
        }
        return self._get_page_view_values(purchase_request, access_token, values, 'my_purchase_request_history', False, **kwargs)

    def _get_purchase_requests_domain(self):
        return []

    @http.route(['/my/purchase_requests', '/my/purchase_requests/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_purchase_request(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        PurchaseRequest = request.env['purchase.request']

        domain = self._get_purchase_requests_domain()

        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'date_start desc'},
            'name': {'label': _('Reference'), 'order': 'name desc'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('date_start', '>', date_begin), ('date_start', '<=', date_end)]

        # count for pager
        purchase_request_count = PurchaseRequest.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/purchase_requests",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=purchase_request_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        purchase_requests = PurchaseRequest.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_purchase_request_history'] = purchase_requests.ids[:100]

        values.update({
            'date': date_begin,
            'purchase_requests': purchase_requests,
            'page_name': 'purchase_request',
            'pager': pager,
            'default_url': '/my/purchase_requests',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby':filterby,
        })
        return request.render("purchase_portal.portal_my_purchase_requests", values)

    @http.route(['/my/purchase_requests/<int:purchase_request>'], type='http', auth="public", website=True)
    def portal_my_purchase_requests_detail(self, purchase_request, access_token=None, report_type=None, download=False, **kw):
        try:
            purchase_request_sudo = self._document_check_access('purchase.request', purchase_request, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._purchase_request_get_page_view_values(purchase_request_sudo, access_token, **kw)

        return request.render("purchase_portal.portal_purchase_request_page", values)
    
    @http.route(['/my/new_purchase_request', '/my/new_purchase_request/<int:purchase_request>'], type='http', auth="public", website=True)
    def portal_my_new_purchase_requests_detail(self, purchase_request=None, access_token=None, report_type=None, download=False, **kw):
        if not purchase_request and kw and kw.get('property_id', False):
            property_id = kw.get('property_id', False)
            purchase_request = request.env['purchase.request'].create({
                'property_id': property_id,
            })
            return request.redirect('/my/new_purchase_request/%s' % purchase_request.id)
        if not purchase_request:
            values = values = {
                'page_name': 'purchase_request',
                'purchase_request': False,
            }
        else:
            try:
                purchase_request_sudo = self._document_check_access('purchase.request', purchase_request, access_token)
            except (AccessError, MissingError):
                return request.redirect('/my')

            values = self._purchase_request_get_page_view_values(purchase_request_sudo, access_token, **kw)
        
        allowed_pms_property_ids = request.env.user.get_active_property_ids()
        
        values['current_property_id'] = request.env['pms.property'].browse(allowed_pms_property_ids[0]) if allowed_pms_property_ids else False
        values['allowed_property_ids'] = request.env['pms.property'].browse(allowed_pms_property_ids) if allowed_pms_property_ids else False

        return request.render("purchase_portal.portal_new_purchase_request_page", values)

    # ------------------------------------------------------------
    # My stock pickings
    # ------------------------------------------------------------

    def _stock_picking_get_page_view_values(self, stock_picking, access_token, **kwargs):
        values = {
            'page_name': 'stock_picking',
            'stock_picking': stock_picking,
        }
        return self._get_page_view_values(stock_picking, access_token, values, 'my_stock_picking_history', False, **kwargs)

    def _get_stock_pickings_domain(self):
        return [('picking_type_id.code', '=', 'incoming')]

    @http.route(['/my/stock_pickings', '/my/stock_pickings/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_stock_pickings(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        StockPicking = request.env['stock.picking']

        domain = self._get_stock_pickings_domain()

        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'scheduled_date desc'},
            'name': {'label': _('Reference'), 'order': 'name desc'},
            'origin': {'label': _('Origin'), 'order': 'origin desc'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('scheduled_date', '>', date_begin), ('scheduled_date', '<=', date_end)]

        # count for pager
        stock_picking_count = StockPicking.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/stock_pickings",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=stock_picking_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        stock_pickings = StockPicking.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_stock_picking_history'] = stock_pickings.ids[:100]

        values.update({
            'date': date_begin,
            'stock_pickings': stock_pickings,
            'page_name': 'stock_picking',
            'pager': pager,
            'default_url': '/my/stock_pickings',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby':filterby,
        })
        return request.render("purchase_portal.portal_my_stock_pickings", values)

    @http.route(['/my/stock_pickings/<int:stock_picking>'], type='http', auth="public", website=True)
    def portal_my_stock_pickings_detail(self, stock_picking, access_token=None, report_type=None, download=False, **kw):
        try:
            stock_picking_sudo = self._document_check_access('stock.picking', stock_picking, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._stock_picking_get_page_view_values(stock_picking_sudo, access_token, **kw)

        return request.render("purchase_portal.portal_stock_picking_page", values)