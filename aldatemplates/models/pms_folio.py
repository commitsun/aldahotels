from odoo import api, fields, models


class PmsFolio(models.Model):
    _inherit = "pms.folio"

    @api.model
    def send_exit_mail(self):
        folios = self.env["pms.folio"].search([])
        if folios and all(
            is_exit_auto_mail
            for is_exit_auto_mail in folios.pms_property_id.mapped("is_exit_auto_mail")
        ):
            for folio in folios:
                reservations = folio.reservation_ids.filtered(
                    lambda r: r.checkout == fields.date.today()
                )
                for reservation in reservations:
                    if reservation.state in "done" and reservation.to_send_mail:
                        template = folio.pms_property_id.property_exit_template
                        subject = template._render_field(
                            "subject",
                            [6, 0, folio.id],
                            compute_lang=True,
                            post_process=True,
                        )[folio.id]
                        body = template._render_field(
                            "body_html",
                            [6, 0, folio.id],
                            compute_lang=True,
                            post_process=True,
                        )[folio.id]
                        invitation_mail = (
                            folio.env["mail.mail"]
                            .sudo()
                            .create(
                                {
                                    "subject": subject,
                                    "body_html": body,
                                    "email_from": folio.pms_property_id.partner_id.email,
                                    "email_to": folio.email,
                                }
                            )
                        )
                        invitation_mail.send()
                        for reservation in folio.reservation_ids:
                            reservation.to_send_mail = False
