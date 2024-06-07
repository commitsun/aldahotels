# Copyright 2024 OsoTranquilo
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

class PmsPropertyRegion(models.Model):
    _inherit = "pms.property"

    cod_region = fields.One2many(
        comodel_name="pms.property.region.assignment",
        inverse_name="pms_property_id",
        string="Region PMS - employees",
        help="The region associated with this property",
    )

    employee_id = fields.Many2one(
        'pms.region', 
        string='Regional Manager', 
        compute='_compute_employee_id',
        store=True
    )

    @api.depends('cod_region')
    def _compute_employee_id(self):
        for property in self:
            if property.cod_region:
                region_assignment = property.cod_region[0]
                region = self.env['pms.property.region'].sudo().search([('cod_region', '=', region_assignment.cod_region)], limit=1)
                # region = self.env['pms.property.region'].sudo().search([('cod_region', '=', property.cod_region[0].cod_region)], limit=1)
                if region:
                    property.employee_id = region.employee_id
                else:
                    property.employee_id = False
                