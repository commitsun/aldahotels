# Copyright 2024 OsoTranquilo - José Luis Algara
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    region_ids = fields.One2many(
        comodel_name='pms.property.region',
        inverse_name='employee_id',
        string='Regions'
    )
    
    cod_region = fields.Char(
        string='Region Code',
        compute='_compute_cod_region'
    )

    @api.depends('job_id', 'region_ids')
    def _compute_cod_region(self):
        for employee in self:
            if employee.job_id and employee.job_id.name == 'Regional Manager':
                region = self.env['pms.property.region'].search([('employee_id', '=', employee.id)], limit=1)
                employee.cod_region = region.cod_region if region else 'No region assigned'
            else:
                employee.cod_region = ''