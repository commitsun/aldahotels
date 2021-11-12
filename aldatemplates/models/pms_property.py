from odoo import fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    property_confirmed_template = fields.Many2one(
        string="Confirmation Template",
        comodel_name="mail.template",
        default=lambda self: self.env.ref(
            "aldatemplates.alda_confirmation_email", raise_if_not_found=False
        ),
    )
    property_exit_template = fields.Many2one(
        string="Exit Template",
        comodel_name="mail.template",
        default=lambda self: self.env.ref(
            "aldatemplates.alda_exit_email", raise_if_not_found=False
        ),
    )
    property_canceled_template = fields.Many2one(
        string="Cancellation Template",
        comodel_name="mail.template",
        default=lambda self: self.env.ref(
            "aldatemplates.alda_cancelation_email", raise_if_not_found=False
        ),
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
