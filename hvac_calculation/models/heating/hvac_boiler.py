from odoo import models, fields, api


class HVACBoiler(models.Model):
    _name = "hvac.boiler"
    _description = "HVAC Boiler"
    _order = "kw_output asc"

    name = fields.Char(string="Boiler Name", required=True)
    
    boiler_type = fields.Selection([
        ('wall', 'Wall Mounted'),
        ('floor', 'Floor Standing'),
        ('combi', 'Combi Boiler'),
        ('system', 'System Boiler'),
    ], string="Type", default='wall')
    
    fuel_type = fields.Selection([
        ('gas', 'Natural Gas'),
        ('lpg', 'LPG'),
        ('oil', 'Oil'),
        ('electric', 'Electric'),
    ], string="Fuel Type", default='gas')
    
    brand = fields.Char(string="Brand")
    model = fields.Char(string="Model")
    
    kw_output = fields.Float(string="Output (kW)", required=True)
    kw_input = fields.Float(string="Input (kW)")
    efficiency = fields.Float(string="Efficiency (%)", default=92)
    
    price = fields.Float(string="Price", required=True)
    
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.name} ({rec.kw_output} kW)"
            result.append((rec.id, name))
        return result
