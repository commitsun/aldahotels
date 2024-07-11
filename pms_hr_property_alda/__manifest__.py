# Copyright 2024 OsoTranquilo - José Luis Algara
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) 
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'PMS HR Property Alda',
    'version': '14.0.1.0.0',
    'category': 'PMS/HR',
    "summary": """ Region and Staff associated with the property """,
    "author": "Irlui Ramirez,José Luis Algara,Odoo Community Association (OCA)",
    "depends": ["base", "pms", "hr"],
    'data': [
        'views/pms_hr_property_view.xml',
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "AGPL-3",
}