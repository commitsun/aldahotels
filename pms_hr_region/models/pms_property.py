# Copyright 2024 OsoTranquilo - José Luis Algara
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PmsPropertyRegion(models.Model):
    _inherit = "pms.property"
    _rec_name = 'name'

    region_info = fields.Text(string="Region Information", compute="_compute_region_info", store=False)

    def _compute_region_info(self):
        for property_rec in self:
            region_info = ""
            region_assignment = self.env['pms.property.region.assignment'].sudo().search([
                ('property_id', '=', property_rec.id)
            ], limit=1)
            if region_assignment:
                region = self.env['pms.property.region'].sudo().search([
                ('id', '=', region_assignment.region_id.id)
            ], limit=1)
                region_info += f"Region ID: {region.cod_region}\n"
                region_info += f"Regional Manager: {region.employee_id.name}\n"
                region_info += f"Revenue Manager: {region_assignment.rvm_employee1_id.name}\n"
                region_info += f"TAZ: {region_assignment.taz_employee_id.name}\n"
                region_info += f"TAZ: {region_assignment.taz2_employee_id.name}\n"
                region_info += f"TMZ: {region_assignment.tmz_employee_id.name}\n"
                region_info += f"TMZ: {region_assignment.tmz2_employee_id.name}\n"
            else:
                region_info = "No region information available."
            property_rec.region_info = region_info
    
    def action_open_region_form(self):
        self.ensure_one()
        region_assignment = self.env['pms.property.region.assignment'].sudo().search([
            ('property_id', '=', self.id)
        ], limit=1)
        if region_assignment:
            region_id = region_assignment.region_id.id
        else:
            region_id = False

        return {
            'type': 'ir.actions.act_window',
            'name': 'Region',
            'res_model': 'pms.property.region',
            'view_mode': 'form',
            'res_id': region_id,
            'target': 'new',
        }
                