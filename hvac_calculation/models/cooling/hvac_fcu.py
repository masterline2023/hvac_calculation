from odoo import models, fields, api


class HVACFCU(models.Model):
    _name = "hvac.fcu"
    _description = "HVAC Fan Coil Unit"
    _order = "cooling_capacity_kw asc"

    name = fields.Char(string="FCU Name", required=True)
    
    fcu_type = fields.Selection([
        ('ceiling_concealed', 'Ceiling Concealed'),
        ('ceiling_exposed', 'Ceiling Exposed'),
        ('wall_mounted', 'Wall Mounted'),
        ('floor_standing', 'Floor Standing'),
        ('cassette', 'Cassette'),
    ], string="Type", default='ceiling_concealed')
    
    brand = fields.Char(string="Brand")
    model = fields.Char(string="Model")
    
    # Capacity
    cooling_capacity_kw = fields.Float(string="Cooling Capacity (kW)", required=True)
    cooling_capacity_btu = fields.Float(string="Cooling Capacity (BTU/hr)", compute="_compute_capacity_btu", store=True)
    cooling_capacity_ton = fields.Float(string="Cooling Capacity (TR)", compute="_compute_capacity_ton", store=True)
    heating_capacity_kw = fields.Float(string="Heating Capacity (kW)")
    
    # Airflow
    airflow_cfm = fields.Float(string="Airflow (CFM)")
    airflow_cmh = fields.Float(string="Airflow (m³/hr)", compute="_compute_airflow_cmh", store=True)
    
    # Fan Speeds
    fan_speeds = fields.Selection([
        ('2', '2 Speeds'),
        ('3', '3 Speeds'),
        ('4', '4 Speeds'),
        ('ec', 'EC Motor (Variable)'),
    ], string="Fan Speeds", default='3')
    
    # Power
    power_input_w = fields.Float(string="Power Input (W)")
    
    # Electrical
    voltage = fields.Selection([
        ('220', '220V Single Phase'),
        ('380', '380V Three Phase'),
    ], string="Voltage", default='220')
    
    price = fields.Float(string="Price", required=True)
    
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")

    @api.depends("cooling_capacity_kw")
    def _compute_capacity_btu(self):
        for rec in self:
            rec.cooling_capacity_btu = rec.cooling_capacity_kw * 3412 if rec.cooling_capacity_kw else 0

    @api.depends("cooling_capacity_kw")
    def _compute_capacity_ton(self):
        for rec in self:
            rec.cooling_capacity_ton = rec.cooling_capacity_kw / 3.517 if rec.cooling_capacity_kw else 0

    @api.depends("airflow_cfm")
    def _compute_airflow_cmh(self):
        for rec in self:
            rec.airflow_cmh = rec.airflow_cfm * 1.699 if rec.airflow_cfm else 0

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.name} ({rec.cooling_capacity_kw:.1f} kW / {rec.cooling_capacity_btu:.0f} BTU)"
            result.append((rec.id, name))
        return result
