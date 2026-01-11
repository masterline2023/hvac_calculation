from odoo import models, fields


class HVACTerms(models.Model):
    _name = "hvac.terms"
    _description = "HVAC Terms and Conditions Template"
    _order = "name"

    name = fields.Char(string="Template Name", required=True)
    
    # Applicable to which sections
    apply_heating = fields.Boolean(string="Apply to Heating", default=True)
    apply_cooling = fields.Boolean(string="Apply to Cooling", default=True)
    apply_hotwater = fields.Boolean(string="Apply to Hot Water", default=True)
    
    offer_includes = fields.Html(string="The Offer Includes")
    offer_excludes = fields.Html(string="The Offer Doesn't Include")
    payment_terms = fields.Html(string="Payment Terms")
    execution_time = fields.Html(string="Execution Time")
    warranty = fields.Html(string="Warranty")
    additional_notes = fields.Html(string="Additional Notes")
    
    active = fields.Boolean(default=True)
