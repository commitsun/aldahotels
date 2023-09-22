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
from lxml import etree
from lxml.html import builder as html

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
from odoo.addons.base.models.ir_mail_server import MailDeliveryException


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _inherit = ['purchase.request', 'portal.mixin']

    property_id = fields.Many2one('pms.property', string='Property')

    def get_portal_url(self):
        res = super(PurchaseRequest, self).get_portal_url()
        portal_link = '/my/purchase_requests/%s' % (self.id) + res
        if self.state in ["to_approve", "draft"] and not self.review_ids.filtered(lambda r: r.status == 'approved'):
            portal_link = '/my/new_purchase_request/%s' % (self.id) + res
        return portal_link

    def request_validation(self):
        res = super(PurchaseRequest, self).request_validation()
        if res.reviewer_ids:
            text = _("A new review %s has been asigned to you." % self.display_name)
            message = html.DIV(
                html.P(_('Hello,')),
                html.P(text)
            )
            body = etree.tostring(message)

            mail_fattura = self.env['mail.mail'].sudo().with_context(wo_bounce_return_path=True).create({
                'subject': _('A new review has been asigned to you'),
                'body_html': body,
                'recipient_ids': res.reviewer_ids.mapped('partner_id'),
                'author_id': self.env.user.partner_id.id,
            })
            try:
                mail_fattura.send(raise_exception=True)
                self.message_post(
                    body=(_("Mail sent for requested review on %s by %s") % (fields.Datetime.now(), self.env.user.display_name))
                    )
            except MailDeliveryException as error:
                self.message_post(
                    body=(_("Error when sending mail for requested review: %s") % (error.args[0]))
                    )
        return res


class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    property_id = fields.Many2one('pms.property', related="request_id.property_id", string='Property', store=True)
    suggested_supplier_id = fields.Many2one('res.partner', string='Suggested Supplier')

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
            min_cost_productinfo = product.seller_ids.filtered(lambda x: x.name.id in request.property_id.seller_ids.ids).sorted(key=lambda r: r.price)[0]
            values['suggested_supplier_id'] = min_cost_productinfo.name.id
            #min_qty = product.seller_ids.filtered(lambda x: x.name.id == request.property_id.seller_id.id).min_qty
            min_qty = min_cost_productinfo.min_qty

            if product_qty < min_qty:
                raise UserError(_('The minimum quantity for this product is %s' % min_qty))
            if request.review_ids:
                request.message_post(body=_('New line added by {user}: <strong> {product} ({quantity})</strong>'.format(user=self.env.user.name, product=product.name, quantity=product_qty)))
        return super().create(values)

    def write(self, vals):
        ctx = self.env.context.copy()
        portal = ctx.get('portal', False)
        product_qty = vals.get('product_qty', False)
        no_msg = ctx.get('no_msg', False)
        if portal and product_qty:
            min_cost_productinfo = self.product_id.seller_ids.filtered(lambda x: x.name.id in self.request_id.property_id.seller_ids.ids).sorted(key=lambda r: r.price)[0]
            vals['suggested_supplier_id'] = min_cost_productinfo.name.id
            #min_qty = self.product_id.seller_ids.filtered(lambda x: x.name.id == self.request_id.property_id.seller_id.id).min_qty
            min_qty = min_cost_productinfo.min_qty
            if product_qty < min_qty:
                raise UserError(_('The minimum quantity for this product is %s' % min_qty))
            if self.request_id.review_ids and not no_msg:
                self.request_id.message_post(body=_('Line edited by {user}: <strong>{product} ({old_quantity} -> {quantity})</strong>'.format(user=self.env.user.name, product=self.product_id.name, old_quantity=self.product_qty, quantity=product_qty)))
        return super().write(vals)

    def unlink(self):
        if self.request_id.review_ids:
            self.request_id.message_post(body=_('Line deleted by {user}: <strong> {product}</strong>'.format(user=self.env.user.name, product=self.product_id.name)))
        return super().unlink()
