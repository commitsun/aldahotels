from odoo import fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    property_confirmed_template = fields.Many2one(
        string="Confirmation Email",
        comodel_name="mail.template",
    )
    property_exit_template = fields.Many2one(
        string="Exit Email",
        comodel_name="mail.template",
    )
    property_canceled_template = fields.Many2one(
        string="Cancellation Email",
        comodel_name="mail.template",
    )
    image1 = fields.Char(string="Image City", attachment=True, store=True)
    image2 = fields.Char(string="Image Property", attachment=True, store=True)
    text_image1 = fields.Html(
        string="Text Image City",
    )
    text_image2 = fields.Html(string="Text Image Property")
    web_city_information_url = fields.Char(string="Web City Info URL")
    quiz_url = fields.Char(string="Quiz URL")
    is_exit_auto_mail = fields.Boolean(string="Auto send mail")
