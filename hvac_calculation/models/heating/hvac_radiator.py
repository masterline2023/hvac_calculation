from odoo import models, fields, api


class HVACRadiator(models.Model):
    _name = "hvac.radiator"
    _description = "HVAC Radiator"
    _order = "radiator_type, height, watt_output"

    name = fields.Char(string="Radiator Name", required=True)
    
    radiator_type = fields.Selection([
        ('aluminum', 'Aluminum Radiator'),
        ('steel', 'Steel Panel Radiator'),
        ('cast_iron', 'Cast Iron Radiator'),
        ('towel', 'Towel Radiator'),
    ], string="Type", required=True, default='aluminum')
    
    brand = fields.Char(string="Brand")
    model = fields.Char(string="Model")
    
    height = fields.Integer(string="Height (mm)")
    width = fields.Integer(string="Width (mm)")
    depth = fields.Integer(string="Depth (mm)")
    
    size_display = fields.Char(
        string="Size",
        compute="_compute_size_display",
        store=True
    )
    
    watt_output = fields.Float(string="Thermal Output (W)", required=True)
    sections = fields.Integer(string="Sections")
    
    price = fields.Float(string="Unit Price", required=True)
    
    active = fields.Boolean(default=True)
    color = fields.Char(string="Color", default="White")
    notes = fields.Text(string="Notes")

    @api.depends("height", "width")
    def _compute_size_display(self):
        for rec in self:
            if rec.height and rec.width:
                rec.size_display = f"{rec.height} x {rec.width}"
            else:
                rec.size_display = ""

    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            if rec.watt_output:
                name += f" ({rec.watt_output:.0f} W)"
            if rec.size_display:
                name += f" [{rec.size_display}]"
            result.append((rec.id, name))
        return result
