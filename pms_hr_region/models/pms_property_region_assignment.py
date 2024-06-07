from odoo import models, fields, api

class PMSPropertyRegionAssignment(models.Model):
    _name = 'pms.property.region.assignment'
    _description = 'PMS Property Region Assignment'

    cod_region = fields.Many2one('pms.property.region', string='Region', required=True,store=True)
    
    pms_property_id = fields.Many2one('pms.property', string='Property', required=True, store=True)
    
    position1_id = fields.Many2one('hr.job', string='RVM', default=14, readonly=True)
    employee1_id = fields.Many2one('hr.employee', string='Employee 1', domain="[('job_id', '=', position1_id)]")

    position2_id = fields.Many2one('hr.job', string='TAZ', default=11, readonly=True)
    employee2_id = fields.Many2one('hr.employee', string='Employee 2', domain="[('job_id', '=', position2_id)]")

    position3_id = fields.Many2one('hr.job', string='TAZ 2', default=11, readonly=True)
    employee3_id = fields.Many2one('hr.employee', string='Employee 3', domain="[('job_id', '=', position3_id)]")

    position4_id = fields.Many2one('hr.job', string='TMZ', default=10, readonly=True)
    employee4_id = fields.Many2one('hr.employee', string='Employee 4', domain="[('job_id', '=', position4_id)]")

    position5_id = fields.Many2one('hr.job', string='TMZ 2', default=10, readonly=True)
    employee5_id = fields.Many2one('hr.employee', string='Employee 5', domain="[('job_id', '=', position5_id)]")

    @api.depends('position1_id')
    def _compute_position1_name(self):
        for record in self:
            record.position1_name = record.position1_id.name if record.position1_id else ''

    @api.onchange('employee2_id')
    def _onchange_employee2_id(self):
        if self.employee2_id:
            return {
                'domain': {
                    'employee3_id': [
                        ('job_id', '=', self.position3_id.id),
                        ('id', '!=', self.employee2_id.id)
                    ]
                }
            }
        else:
            return {
                'domain': {
                    'employee3_id': [('job_id', '=', self.position3_id.id)]
                }
            }
    @api.onchange('employee3_id')
    def _onchange_employee3_id(self):
        if self.employee3_id:
            return {
                'domain': {
                    'employee2_id': [
                        ('job_id', '=', self.position2_id.id),
                        ('id', '!=', self.employee3_id.id)
                    ]
                }
            }
        else:
            return {
                'domain': {
                    'employee3_id': [('job_id', '=', self.position2_id.id)]
                }
            }
    
    @api.onchange('employee4_id')
    def _onchange_employee4_id(self):
        if self.employee4_id:
            return {
                'domain': {
                    'employee5_id': [
                        ('job_id', '=', self.position5_id.id),
                        ('id', '!=', self.employee4_id.id)
                    ]
                }
            }
        else:
            return {
                'domain': {
                    'employee5_id': [('job_id', '=', self.position5_id.id)]
                }
            }
    @api.onchange('employee5_id')
    def _onchange_employee5_id(self):
        if self.employee5_id:
            return {
                'domain': {
                    'employee4_id': [
                        ('job_id', '=', self.position4_id.id),
                        ('id', '!=', self.employee5_id.id)
                    ]
                }
            }
        else:
            return {
                'domain': {
                    'employee5_id': [('job_id', '=', self.position4_id.id)]
                }
            }