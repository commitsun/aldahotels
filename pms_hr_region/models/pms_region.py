# Copyright 2024 OsoTranquilo - José Luis Algara
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Region(models.Model):
    _name = 'pms.property.region'
    _description = 'PMS Property Region'
    _rec_name = 'cod_region'

    cod_region = fields.Char(
        string='Region Code', 
        compute='_compute_region_code', 
        store=True, 
        ondelete='cascade')

    employee_id = fields.Many2one(
        comodel_name='hr.employee', 
        string='Regional Manager', 
        store=True, 
        domain="[('job_id', '=', 4)]"
    )

    property_ids = fields.One2many(
        comodel_name='pms.property.region.assignment',
        inverse_name='region_id', 
        string='Property Staff Register'
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        help="Company to which the region belongs",
        required=True,
        store=True
    )

    assigned_properties = fields.Many2many(
        'pms.property', compute='_compute_assigned_properties', store=False
    )

    @api.onchange('company_id')
    def _compute_available_properties(self):
        for region in self:
            if region.company_id:
                try:
                    # assigned_properties = self.env['pms.property.region.assignment'].search([]).mapped('property_id.id')
                    assigned_properties = (
                        self.env['pms.property.region.assignment']
                        .search([('active', '=', True)])
                        .mapped('property_id.id')
                    )
                    available_properties = self.env['pms.property'].sudo().search([
                        ('company_id', '=', region.company_id.id),
                        ('id', 'not in', assigned_properties)
                    ])
                    if available_properties:
                        return {
                            'domain': {
                                'property_ids.property_id': [('company_id', '=', region.company_id.id), ('id', 'in', available_properties)]
                            }
                        }
                    else: raise ValidationError('All properties have been assigned')
                except Exception as e:
                    raise ValidationError(f"An error occurred while updating available properties: {e}")

    @api.depends('property_ids')
    def _compute_assigned_properties(self):
        for region in self:
            region.assigned_properties = region.property_ids.mapped('property_id')

    @api.depends('employee_id', 'company_id')
    def _compute_region_code(self):
        for region in self:
            base_code = 'RGM'
            total_regions = self.env['pms.property.region'].search_count([])
            company_id = region.company_id.name or ''
            employee_id = region.employee_id.name or ''
            region.cod_region = '{}-{}'.format(company_id, employee_id)

    @api.constrains('employee_id', 'company_id')
    def _check_unique_region(self):
        for record in self:
            if record.employee_id and record.company_id:
                existing_region = self.search([
                    ('employee_id', '=', record.employee_id.id),
                    ('company_id', '=', record.company_id.id),
                    ('id', '!=', record.id)
                ], limit=1)
                if existing_region:
                    raise ValidationError('This employee is already assigned as a Regional Manager in another region for the same company.')

    @api.constrains('property_ids')
    def _check_duplicate_property_id(self):
        for region in self:
            property_ids = region.property_ids.mapped('property_id')
            if len(property_ids) != len(set(property_ids.ids)):
                raise ValidationError('A property cannot be assigned to multiple regions.')

    @api.onchange('region_id')
    def _avalable_property_ids(self):
        for region in self:
            property_ids = region.property_ids.mapped('property_id')
            if len(property_ids) != len(set(property_ids.ids)):
                raise ValidationError('A property cannot be assigned to multiple regions.')


    def _get_default_kanban_view(self):
        return self.env.ref('pms_hr_region.view_region_kanban').id

    kanban_view_id = fields.Many2one('ir.ui.view', string="Kanban View", default=_get_default_kanban_view)
