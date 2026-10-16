# Copyright 2026 Alex Abbas Deselaers (Skanndar)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Base Location Geonames Import Municipality",
    "version": "19.0.1.0.0",
    "category": "Partner Management",
    "summary": "Name imported cities after their municipality (admin3), "
    "keeping the place in parentheses",
    "author": "Skanndar, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/partner-contact",
    "license": "AGPL-3",
    "depends": ["base_location_geonames_import"],
    "data": ["wizard/geonames_import_view.xml"],
    "installable": True,
}
