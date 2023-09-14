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

from datetime import datetime
from uuid import uuid4
import pytz

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _inherit = ['purchase.request', 'portal.mixin']

    property_id = fields.Many2one('pms.property', string='Property')

    def get_portal_url(self):
        res = super(PurchaseRequest, self).get_portal_url()
        portal_link = '/my/purchase_requests/%s' % (self.id) + res
        if self.is_editable:
            portal_link = '/my/new_purchase_request/%s' % (self.id) + res
        return portal_link


class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    property_id = fields.Many2one('pms.property', related="request_id.property_id", string='Property', store=True)

    @api.model
    def create(self, values):
        ctx = self.env.context.copy()
        portal = ctx.get('portal', False)
        if portal:
            request_id = values.get('request_id', False)
            product_id = values.get('product_id', False)
            product_qty = values.get('product_qty', False)
            
            request = self.env['purchase.request'].browse(request_id)
            product = self.env['product.product'].browse(product_id)
            min_qty = product.seller_ids.filtered(lambda x: x.name.id == request.property_id.seller_id.id).min_qty

            if product_qty < min_qty:
                raise UserError(_('The minimum quantity for this product is %s' % min_qty))
        return super().create(values)
    
    def write(self, vals):
        ctx = self.env.context.copy()
        portal = ctx.get('portal', False)
        product_qty = vals.get('product_qty', False)
        if portal and product_qty:
            min_qty = self.product_id.seller_ids.filtered(lambda x: x.name.id == self.request_id.property_id.seller_id.id).min_qty
            if product_qty < min_qty:
                raise UserError(_('The minimum quantity for this product is %s' % min_qty))
        return super().write(vals)
