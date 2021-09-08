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
    image1 = fields.Binary(
        string="Image 1",
        attachment=True,
        store=True
    )
    image2 = fields.Binary(
        string="Image 2",
        attachment=True,
        store=True
    )
    text_image1 = fields.Html(string="Text Image 1",)
    text_image2 = fields.Html(string="Text Image 2")
    web_city_information = fields.Char(string="Web City Information")
