from odoo import models, fields, api


class HVACAHU(models.Model):
    _name = "hvac.ahu"
    _description = "HVAC Air Handling Unit"
    _order = "airflow_cfm asc"

    name = fields.Char(string="AHU Name", required=True)
    
    ahu_type = fields.Selection([
        ('standard', 'Standard AHU'),
        ('rooftop', 'Rooftop Unit'),
        ('doas', 'Dedicated Outdoor Air'),
        ('heat_recovery', 'Heat Recovery AHU'),
    ], string="Type", default='standard')
    
    brand = fields.Char(string="Brand")
    model = fields.Char(string="Model")
    
    # Airflow
    airflow_cfm = fields.Float(string="Airflow (CFM)", required=True)
    airflow_cmh = fields.Float(string="Airflow (m³/hr)", compute="_compute_airflow_cmh", store=True)
    
    # Capacity
    cooling_capacity_kw = fields.Float(string="Cooling Capacity (kW)")
    cooling_capacity_ton = fields.Float(string="Cooling Capacity (TR)", compute="_compute_capacity_ton", store=True)
    heating_capacity_kw = fields.Float(string="Heating Capacity (kW)")
    
    # Fan
    fan_power_kw = fields.Float(string="Fan Power (kW)")
    static_pressure_pa = fields.Float(string="Static Pressure (Pa)")
    
    # Electrical
    voltage = fields.Selection([
        ('220', '220V Single Phase'),
        ('380', '380V Three Phase'),
        ('400', '400V Three Phase'),
    ], string="Voltage", default='380')
    
    price = fields.Float(string="Price", required=True)
    
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")

    @api.depends("airflow_cfm")
    def _compute_airflow_cmh(self):
        for rec in self:
            rec.airflow_cmh = rec.airflow_cfm * 1.699 if rec.airflow_cfm else 0

    @api.depends("cooling_capacity_kw")
    def _compute_capacity_ton(self):
        for rec in self:
            rec.cooling_capacity_ton = rec.cooling_capacity_kw / 3.517 if rec.cooling_capacity_kw else 0

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.name} ({rec.airflow_cfm:.0f} CFM)"
            if rec.cooling_capacity_ton:
                name += f" - {rec.cooling_capacity_ton:.1f} TR"
            result.append((rec.id, name))
        return result
