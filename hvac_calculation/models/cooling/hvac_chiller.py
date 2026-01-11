from odoo import models, fields, api


class HVACChiller(models.Model):
    _name = "hvac.chiller"
    _description = "HVAC Chiller"
    _order = "cooling_capacity_kw asc"

    name = fields.Char(string="Chiller Name", required=True)
    
    chiller_type = fields.Selection([
        ('air_cooled', 'Air Cooled'),
        ('water_cooled', 'Water Cooled'),
        ('absorption', 'Absorption'),
    ], string="Type", default='air_cooled')
    
    brand = fields.Char(string="Brand")
    model = fields.Char(string="Model")
    
    # Capacity
    cooling_capacity_kw = fields.Float(string="Cooling Capacity (kW)", required=True)
    cooling_capacity_ton = fields.Float(string="Cooling Capacity (TR)", compute="_compute_capacity_ton", store=True)
    cooling_capacity_btu = fields.Float(string="Cooling Capacity (BTU/hr)", compute="_compute_capacity_btu", store=True)
    
    # Power
    power_input_kw = fields.Float(string="Power Input (kW)")
    cop = fields.Float(string="COP", help="Coefficient of Performance")
    eer = fields.Float(string="EER", help="Energy Efficiency Ratio")
    
    # Electrical
    voltage = fields.Selection([
        ('220', '220V Single Phase'),
        ('380', '380V Three Phase'),
        ('400', '400V Three Phase'),
    ], string="Voltage", default='380')
    
    price = fields.Float(string="Price", required=True)
    
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")

    @api.depends("cooling_capacity_kw")
    def _compute_capacity_ton(self):
        for rec in self:
            rec.cooling_capacity_ton = rec.cooling_capacity_kw / 3.517 if rec.cooling_capacity_kw else 0

    @api.depends("cooling_capacity_kw")
    def _compute_capacity_btu(self):
        for rec in self:
            rec.cooling_capacity_btu = rec.cooling_capacity_kw * 3412 if rec.cooling_capacity_kw else 0

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.name} ({rec.cooling_capacity_kw:.1f} kW / {rec.cooling_capacity_ton:.1f} TR)"
            result.append((rec.id, name))
        return result
