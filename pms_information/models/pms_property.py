# Copyright 2024 OsoTranquilo - José Luis Algara
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PmsProperty(models.Model):
    _inherit = "pms.property"

    pms_property_information_ids = fields.One2many(
        comodel_name='pms.property.information', 
        inverse_name='pms_property_id', 
        string='Property Information'
    )


