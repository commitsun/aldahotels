# Copyright 2024 OsoTranquilo - José Luis Algara
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PmsPropertyInformation(models.Model):
    _name = 'pms.property.information'
    _description = 'PMS Property Information'

    pms_property_id = fields.Many2one(
        comodel_name='pms.property', 
        string='Property', 
        required=True, 
        ondelete='cascade'
    )
    #contar las habitaciones  
    total_rooms = fields.Integer(string='Total de Habitaciones', compute='_compute_total_rooms')
    #definir cantidad de habitaciones "en turismo"
    total_tourism_rooms = fields.Integer(
        string='Tourism Rooms',
    )
    open_date = fields.Datetime(
        string='Open date',
        default=fields.Datetime.now,
    )
    #date = fields.Date(string="Date", required=True, default=fields.Date.context_today)
    # Campos calculados para el estado del hotel
    is_ramp_up = fields.Boolean(
        string='Ramp-Up', 
        compute='_compute_state', 
        default=True,
    )
    is_ramp_rate = fields.Boolean(
        string='Ramp-Rate', 
        compute='_compute_state',
        default=False,
    )
    months_to_ramp_rate = fields.Integer(
        string='Month to Ramp-Rate', 
        compute='_compute_months_to_ramp_rate'
    )

    @api.depends('open_date')
    def _compute_total_rooms(self):
        for record in self:
            target_rooms = (
                self.env["pms.room"]
                .with_context(active_test=True)
                .sudo().search([("pms_property_id", "=", record.id)])
            )
            record.total_rooms = len(target_rooms)

    @api.constrains('total_tourism_rooms')
    def _check_total_tourism_rooms(self):
        for record in self:
            if record.total_tourism_rooms > record.total_rooms:
                raise ValidationError(
                    'The number of tourist rooms cannot exceed the total number of rooms.'
                )

    @api.depends('open_date')
    def _compute_state(self):
        for record in self:
            if record.open_date:
                open_date = fields.Date.from_string(record.open_date)
                today = fields.Date.context_today(self)
                #today = fields.Date.today()
                diff_months = (today.year - open_date.year) * 12 + today.month - open_date.month
                record.is_ramp_up = diff_months < 17
                record.is_ramp_rate = diff_months >= 17
            else:
                record.is_ramp_up = False
                record.is_ramp_rate = False
    
    @api.depends('open_date')
    def _compute_months_to_ramp_rate(self):
        for record in self:
            if record.open_date:
                open_date = fields.Date.from_string(record.open_date)
                today = fields.Date.context_today(self)
                diff_months = (today.year - open_date.year) * 12 + today.month - open_date.month
                if diff_months < 17:
                    record.months_to_ramp_rate = 17 - diff_months
                else:
                    record.months_to_ramp_rate = 0
            else:
                record.months_to_ramp_rate = 0