# Copyright 2024 OsoTranquilo - José Luis Algara
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo import models, fields, api

class PMSPropertyRegionAssignment(models.Model):
    _name = 'pms.property.region.assignment'
    _description = 'PMS Property Region Assignment'

    region_id = fields.Many2one(
        comodel_name='pms.property.region', 
        string='Region', 
        required=True,
        store=True, 
        ondelete='cascade'
    )
    property_id = fields.Many2one(
        comodel_name='pms.property', 
        string='Property', 
        required=True, 
        store=True
    )
    rvm_position_id = fields.Integer(
        string='RVM Position ID', 
        compute='_compute_position_id', 
        store=True
        )
    taz_position_id = fields.Integer(
        string='TAZ Position ID', 
        compute='_compute_position_id', 
        store=True
    )
    tmz_position_id = fields.Integer(
        string='TMZ Position ID', 
        compute='_compute_position_id', 
        store=True
    )
    rvm_employee1_id = fields.Many2one(
        comodel_name='hr.employee', 
        string='RVM', 
        domain="[('job_id', '=', rvm_position_id)]"
    )
    taz_employee_id = fields.Many2one(
        comodel_name='hr.employee', 
        string='TAZ', 
        domain="[('job_id', '=', taz_position_id)]"
    )
    taz2_employee_id = fields.Many2one(
        comodel_name='hr.employee', 
        string='TAZ', 
        domain="[('job_id', '=', taz_position_id)]"
    )
    tmz_employee_id = fields.Many2one(
        comodel_name='hr.employee', 
        string='TMZ', 
        domain="[('job_id', '=', tmz_position_id)]"
    )
    tmz2_employee_id = fields.Many2one(
        comodel_name='hr.employee', 
        string='TMZ', 
        domain="[('job_id', '=', tmz_position_id)]"
    )
    active = fields.Boolean(
        string='Select',
        default=True,
        help="If unchecked, it will allow you to disable the"
        "Availability the property and staff without it."
    )

    assigned_properties = fields.Many2many(
        'pms.property', compute='_compute_assigned_properties', store=False
    )


    @api.depends('region_id')
    def _compute_position_id(self):
        rvm_position = self.env['hr.job'].sudo().search([('name', '=', 'Revenue Manager')], limit=1)
        taz_position = self.env['hr.job'].sudo().search([('name', '=', 'TAZ')], limit=1)
        tmz_position = self.env['hr.job'].sudo().search([('name', '=', 'TMZ')], limit=1)
        for record in self:
            record.rvm_position_id = rvm_position.id if rvm_position else False
            record.taz_position_id = taz_position.id if taz_position else False
            record.tmz_position_id = tmz_position.id if tmz_position else False

    @api.onchange('active')
    def _onchange_region_id(self):
        if self.region_id:
            assigned_properties = self.env['pms.property.region.assignment'].search([('active', '=', True)]).mapped('property_id.id')
            available_properties = self.env['pms.property'].sudo().search([
                ('company_id', '=', self.region_id.company_id.id),
                ('id', 'not in', assigned_properties)
            ])
            return {
                'domain': {
                    'property_id': [('company_id', '=', self.region_id.company_id.id), ('id', 'in', available_properties.ids)]
                }
            }

    # @api.onchange("active")
    # def _check_is_active(self):
    #     for record in self:
    #         if record.active:
    #             assigned_properties = (
    #                 self.env['pms.property.region.assignment']
    #                 .search([('active', '=', True)])
    #                 .mapped('property_id.id')
    #             )
    #             if assigned_properties:
    #                 return {
    #                     'domain': {
    #                         'property_id': [('id', 'not in', assigned_properties)]
    #                     }
    #                 }

    @api.depends('rvm_position_id')
    def _compute_position1_name(self):
        for record in self:
            record.position1_name = record.rvm_position_id.name if record.rvm_position_id else ''

    @api.onchange('taz_employee_id')
    def _onchange_employee2_id(self):
        if self.taz_employee_id:
            return {
                'domain': {
                    'taz2_employee_id': [
                        ('job_id', '=', self.taz_position_id),
                        ('id', '!=', self.taz_employee_id.id)
                    ]
                }
            }
        else:
            return {
                'domain': {
                    'taz2_employee_id': [('job_id', '=', self.taz_position_id)]
                }
            }

    @api.onchange('taz2_employee_id')
    def _onchange_employee3_id(self):
        if self.taz2_employee_id:
            return {
                'domain': {
                    'taz_employee_id': [
                        ('job_id', '=', self.taz_position_id),
                        ('id', '!=', self.taz2_employee_id.id)
                    ]
                }
            }
        else:
            return {
                'domain': {
                    'taz2_employee_id': [('job_id', '=', self.taz_position_id)]
                }
            }
    
    @api.onchange('tmz_employee_id')
    def _onchange_employee4_id(self):
        if self.tmz_employee_id:
            return {
                'domain': {
                    'tmz2_employee_id': [
                        ('job_id', '=', self.tmz_position_id),
                        ('id', '!=', self.tmz_employee_id.id)
                    ]
                }
            }
        else:
            return {
                'domain': {
                    'tmz2_employee_id': [('job_id', '=', self.tmz2_employee_id.id)]
                }
            }
    @api.onchange('tmz2_employee_id')
    def _onchange_employee5_id(self):
        if self.tmz2_employee_id:
            return {
                'domain': {
                    'tmz_employee_id': [
                        ('job_id', '=', self.tmz_position_id),
                        ('id', '!=', self.tmz2_employee_id.id)
                    ]
                }
            }
        else:
            return {
                'domain': {
                    'tmz2_employee_id': [('job_id', '=', self.tmz_position_id)]
                }
            }