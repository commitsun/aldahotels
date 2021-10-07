# Copyright 2021 Jose Luis Algara Toledo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "product.template"

    # Fields declaration
    is_crib = fields.Boolean("Is a baby crib", default=False)
