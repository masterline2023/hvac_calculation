from odoo import models, fields, api


class HVACPoolHeater(models.Model):
    _name = "hvac.pool.heater"
    _description = "Pool Heater"
    _order = "heating_capacity_kw asc"

    name = fields.Char(string="Heater Name", required=True)
    
    heater_type = fields.Selection([
        ('gas', 'Gas Pool Heater'),
        ('electric', 'Electric Pool Heater'),
        ('heat_pump', 'Pool Heat Pump'),
        ('solar', 'Solar Pool Heater'),
    ], string="Type", required=True, default='heat_pump')
    
    brand = fields.Char(string="Brand")
    model = fields.Char(string="Model")
    
    # Capacity
    heating_capacity_kw = fields.Float(string="Heating Capacity (kW)", required=True)
    heating_capacity_btu = fields.Float(string="Heating Capacity (BTU/hr)", compute="_compute_capacity_btu", store=True)
    
    # Pool Size Range
    min_pool_volume = fields.Float(string="Min Pool Volume (m³)")
    max_pool_volume = fields.Float(string="Max Pool Volume (m³)")
    
    # Power
    power_input_kw = fields.Float(string="Power Input (kW)")
    cop = fields.Float(string="COP", help="For heat pumps")
    
    # Electrical
    voltage = fields.Selection([
        ('220', '220V Single Phase'),
        ('380', '380V Three Phase'),
    ], string="Voltage", default='380')
    
    price = fields.Float(string="Price", required=True)
    
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")

    @api.depends("heating_capacity_kw")
    def _compute_capacity_btu(self):
        for rec in self:
            rec.heating_capacity_btu = rec.heating_capacity_kw * 3412 if rec.heating_capacity_kw else 0

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.name} ({rec.heating_capacity_kw:.1f} kW)"
            result.append((rec.id, name))
        return result


class HVACPoolEquipment(models.Model):
    _name = "hvac.pool.equipment"
    _description = "Pool Equipment"
    _order = "name"

    name = fields.Char(string="Equipment Name", required=True)
    
    equipment_type = fields.Selection([
        ('pump', 'Circulation Pump'),
        ('filter', 'Sand Filter'),
        ('cover', 'Pool Cover'),
        ('controller', 'Pool Controller'),
        ('solar_panel', 'Solar Panel'),
        ('accessory', 'Accessory'),
    ], string="Type", default='pump')
    
    brand = fields.Char(string="Brand")
    model = fields.Char(string="Model")
    
    # Specifications
    flow_rate_cmh = fields.Float(string="Flow Rate (m³/hr)")
    power_kw = fields.Float(string="Power (kW)")
    
    price = fields.Float(string="Price", required=True)
    
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")
