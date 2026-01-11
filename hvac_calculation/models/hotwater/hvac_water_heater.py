from odoo import models, fields, api


class HVACWaterHeater(models.Model):
    _name = "hvac.water.heater"
    _description = "Hot Water Heater"
    _order = "capacity_liters asc"

    name = fields.Char(string="Heater Name", required=True)
    
    heater_type = fields.Selection([
        ('gas_instant', 'Gas Instant'),
        ('gas_storage', 'Gas Storage'),
        ('electric_instant', 'Electric Instant'),
        ('electric_storage', 'Electric Storage'),
        ('solar', 'Solar Water Heater'),
        ('heat_pump', 'Heat Pump Water Heater'),
    ], string="Type", required=True, default='gas_storage')
    
    brand = fields.Char(string="Brand")
    model = fields.Char(string="Model")
    
    # Capacity
    capacity_liters = fields.Float(string="Capacity (Liters)")
    flow_rate_lpm = fields.Float(string="Flow Rate (L/min)", help="For instant heaters")
    
    # Power
    power_kw = fields.Float(string="Power (kW)")
    
    # For Solar
    collector_area_sqm = fields.Float(string="Collector Area (m²)", help="For solar heaters")
    tank_capacity = fields.Float(string="Tank Capacity (L)", help="For solar heaters")
    
    # Electrical
    voltage = fields.Selection([
        ('220', '220V Single Phase'),
        ('380', '380V Three Phase'),
    ], string="Voltage", default='220')
    
    price = fields.Float(string="Price", required=True)
    
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")

    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            if rec.capacity_liters:
                name += f" ({rec.capacity_liters:.0f} L)"
            elif rec.flow_rate_lpm:
                name += f" ({rec.flow_rate_lpm:.0f} L/min)"
            result.append((rec.id, name))
        return result
