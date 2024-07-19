# Copyright 2024 OsoTranquilo - José Luis Algara
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class PmsProperty(models.Model):
    _inherit = "pms.property"

    kpi_id = fields.Many2one('pms.alda.kpis', string='KPI', ondelete='cascade')

    is_ramp_up = fields.Boolean(
        string='Ramp-Up', 
        compute='_compute_state', 
        default=True,
        help="From the opening of a hotel the first 17 months a hotel has RAMP-UP status, from month 17 it has RAMP-RATE status.",
    )
    
    is_ramp_rate = fields.Boolean(
        string='Ramp-Rate', 
        compute='_compute_state',
        default=False,
        help="From the opening of a hotel the first 17 months a hotel has RAMP-UP status, from month 17 it has RAMP-RATE status.",
    )

    months_to_ramp_rate = fields.Integer(
        string='Month to Ramp-Rate', 
        compute='_compute_months_to_ramp_rate',
        help="From the opening of a hotel the first 17 months a hotel has RAMP-UP status, from month 17 it has RAMP-RATE status.",
    )

    @api.depends('kpi_id.kpi_value')
    def _compute_state(self):
        for record in self:
            if record.kpi_id.name == 'ramp_time':  
                if record.open_date:
                    open_date = fields.Datetime.from_string(record.open_date)
                    today = fields.Date.context_today(self)
                    value_kpi = int(record.kpi_id.kpi_value)
                    diff_months = (today.year - open_date.year) * 12 + today.month - open_date.month
                    record.is_ramp_up = diff_months < value_kpi
                    record.is_ramp_rate = diff_months >= 17
                else:
                    record.is_ramp_up = False
                    record.is_ramp_rate = False
            else:
                record.is_ramp_up = False
                record.is_ramp_rate = False
    
    @api.depends('kpi_id.kpi_value')
    def _compute_months_to_ramp_rate(self):
        for record in self:
            if record.kpi_id.name == 'ramp_time': 
                if record.open_date:
                    open_date = fields.Datetime.from_string(record.open_date)
                    today = fields.Date.context_today(self)
                    value_kpi = int(record.kpi_id.kpi_value)
                    diff_months = (today.year - open_date.year) * 12 + today.month - open_date.month
                    if diff_months < value_kpi:
                        record.months_to_ramp_rate = value_kpi - diff_months
                    else:
                        record.months_to_ramp_rate = 0
                else:
                    record.months_to_ramp_rate = 0
            else:
                record.months_to_ramp_rate = 0
