from odoo import fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    confirmation_template_id = fields.Many2one(
        string="Confirmation Template",
        comodel_name="mail.template",
        # default=lambda self: self._get_default_confirmation_template_id(),
    )
    image1 = fields.Binary(string="Image City", attachment=True, store=True)
    image2 = fields.Binary(string="Image Property", attachment=True, store=True)
    text_image1 = fields.Html(
        string="Text Image City",
    )
    text_image2 = fields.Html(string="Text Image Property")
    web_city_information_url = fields.Char(string="Web City Info URL")
    survey_url = fields.Char(string="Survey URL")

    #
    # def _get_default_confirmation_template_id(self):
    #     default_template_id = self.env.ref("aldatemplates.alda_confirmation_email").id
    #     return default_template_id
