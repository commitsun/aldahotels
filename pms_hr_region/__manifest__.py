{
    'name': 'PMS HR Regions Management',
    'version': '14.0.1.0.0',
    'category': 'PMS/HR',
    "summary": """ Region and Staff associated with the property """,
    "author": "Irlui Ramirez,José Luis Algara,Odoo Community Association (OCA)",
    "depends": ["base", "pms", "hr"],
    'data': [
        'views/region_views.xml',
        'views/pms_property_views.xml',
        'views/pms_property_region_assignment_views.xml',
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "AGPL-3",
}