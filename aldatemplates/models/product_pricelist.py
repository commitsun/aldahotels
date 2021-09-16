from odoo import fields, models, api


class ProductPricelist(models.Model):
    """Before creating a 'daily' pricelist, you need to consider the following:
    A pricelist marked as daily is used as a daily rate plan for room types and
    therefore is related only with one property.
    """

    _inherit = "product.pricelist"


    pricelist_email_text = fields.Html(
        string="Pricelist Email Text"
    )
