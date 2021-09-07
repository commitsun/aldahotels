from odoo import fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    confirmation_template = fields.Many2one(
        string="Confirmation Template",
        comodel_name="mail.template",
        default=lambda self: self.env["mail.template"]
        .search([("name", "=", "Alda Confirmation Email")])
        .id,
    )
