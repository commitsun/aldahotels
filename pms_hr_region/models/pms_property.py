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
                    print("AQUIIIIIIIIIIIII........", property.employee_id)
                else:
                    property.employee_id = False
                    print("AQUIIIIIIIIIIIII222222222222222........", property.employee_id)
                

    # @api.model
    # def create(self, vals):
    #     record = super(PmsPropertyRegion, self).create(vals)
    #     record._update_employee_id()
    #     return record

    # def write(self, vals):
    #     result = super(PmsPropertyRegion, self).write(vals)
    #     self._update_employee_id()
    #     return result

    # def _update_employee_id(self):
    #     for property in self:
    #         if property.cod_region:
    #             region = self.env['pms.property.region'].sudo().search([('cod_region', '=', property.cod_region[0].cod_region)], limit=1)
    #             if region:
    #                 # Si employee_id está vacío, inicializa con el valor de region.employee_id
    #                 if not property.employee_id:
    #                     property.employee_id = region.employee_id
    #                 else:
    #                     # Si employee_id tiene un valor, actualiza el region correspondiente
    #                     region.employee_id = property.employee_id
    #         else:
    #             property.employee_id = False

    # @api.model
    # def get_region_employee_list(self):
    #     result = []
    #     property_regions = self.env['pms.property.region'].search([])
        
    #     for region in property_regions:
    #         for assignment in region.property_cod_regions:
    #             if assignment.pms_property_id.id == self.id:
    #                 result.append({
    #                     'region': region.cod_region,
    #                     'employee': region.employee_id.name
    #                 })
    #     return result