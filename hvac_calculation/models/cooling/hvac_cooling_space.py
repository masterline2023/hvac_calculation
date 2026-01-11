from odoo import models, fields, api
import math


class HVACCoolingSpace(models.Model):
    _name = "hvac.cooling.space"
    _description = "Cooling Space/Room"
    _order = "floor_sequence, sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    
    project_id = fields.Many2one(
        "hvac.cooling.project",
        string="Project",
        required=True,
        ondelete="cascade"
    )

    # Location
    floor = fields.Selection([
        ('basement', 'Basement'),
        ('ground', 'Ground Floor'),
        ('first', 'First Floor'),
        ('second', 'Second Floor'),
        ('third', 'Third Floor'),
        ('fourth', 'Fourth Floor'),
        ('roof', 'Roof Floor'),
        ('annex', 'Annex'),
    ], string="Floor", default='ground')
    
    floor_sequence = fields.Integer(string="Floor Sequence", compute="_compute_floor_sequence", store=True)
    room_name = fields.Char(string="Room Name")

    # Dimensions
    area = fields.Float(string="Area (m²)")
    height = fields.Float(string="Height (m)", default=3.0)
    volume = fields.Float(string="Volume (m³)", compute="_compute_volume", store=True)
    
    # Cooling Load Calculation
    watt_per_sqm = fields.Float(string="Watt / m²", default=150, help="Cooling load per square meter")
    btu_per_sqm = fields.Float(string="BTU / m²", compute="_compute_btu_per_sqm", store=True, readonly=False)
    load_factor_percent = fields.Float(string="Load Factor (%)", default=100)
    qty = fields.Integer(string="Room Qty", default=1)
    
    # Calculated Loads
    cooling_load_watt = fields.Float(string="Cooling Load (W)", compute="_compute_cooling_load", store=True)
    cooling_load_btu = fields.Float(string="Cooling Load (BTU/hr)", compute="_compute_cooling_load", store=True)
    cooling_load_ton = fields.Float(string="Cooling Load (TR)", compute="_compute_cooling_load", store=True)

    # System Type
    system_type = fields.Selection([
        ('fcu', 'Fan Coil Unit'),
        ('ahu', 'Air Handling Unit'),
        ('split', 'Split Unit'),
        ('ducted_split', 'Ducted Split'),
        ('cassette', 'Cassette Unit'),
        ('vrf', 'VRF System'),
    ], string="System Type", default='fcu')

    # FCU Selection
    suggested_fcu_id = fields.Many2one("hvac.fcu", string="Suggested FCU", compute="_compute_suggested_fcu", store=True, readonly=False)
    selected_fcu_id = fields.Many2one("hvac.fcu", string="Selected FCU")
    fcu_id = fields.Many2one("hvac.fcu", string="FCU", compute="_compute_final_fcu", store=True)
    
    fcu_capacity = fields.Float(string="FCU Capacity (kW)", related="fcu_id.cooling_capacity_kw", readonly=True)
    suggested_fcu_qty = fields.Integer(string="Suggested FCU Qty", compute="_compute_suggested_fcu_qty", store=True)
    fcu_qty = fields.Integer(string="FCU Qty", default=1)
    fcu_unit_price = fields.Float(string="FCU Unit Price", related="fcu_id.price", readonly=True)
    fcu_subtotal = fields.Float(string="FCU Subtotal", compute="_compute_fcu_subtotal", store=True)

    # Thermostat
    thermostat_price = fields.Float(string="Thermostat Price", default=3000)
    thermostat_qty = fields.Integer(string="Thermostat Qty", compute="_compute_thermostat_qty", store=True)
    thermostat_subtotal = fields.Float(string="Thermostat Total", compute="_compute_thermostat_subtotal", store=True)
    
    # Space Subtotal
    space_subtotal = fields.Float(string="Space Subtotal", compute="_compute_space_subtotal", store=True)

    notes = fields.Text(string="Notes")

    # Computed Methods
    @api.depends("floor")
    def _compute_floor_sequence(self):
        floor_order = {'basement': 1, 'ground': 2, 'first': 3, 'second': 4, 'third': 5, 'fourth': 6, 'roof': 7, 'annex': 8}
        for rec in self:
            rec.floor_sequence = floor_order.get(rec.floor, 99)

    @api.depends("area", "height")
    def _compute_volume(self):
        for rec in self:
            rec.volume = (rec.area or 0) * (rec.height or 3.0)

    @api.depends("watt_per_sqm")
    def _compute_btu_per_sqm(self):
        for rec in self:
            rec.btu_per_sqm = rec.watt_per_sqm * 3.412 if rec.watt_per_sqm else 0

    @api.depends("area", "watt_per_sqm", "load_factor_percent", "qty")
    def _compute_cooling_load(self):
        for rec in self:
            load_factor = (rec.load_factor_percent or 100) / 100
            rec.cooling_load_watt = (rec.area or 0) * (rec.watt_per_sqm or 150) * load_factor * (rec.qty or 1)
            rec.cooling_load_btu = rec.cooling_load_watt * 3.412
            rec.cooling_load_ton = rec.cooling_load_watt / 3517

    @api.depends("cooling_load_watt", "system_type")
    def _compute_suggested_fcu(self):
        for rec in self:
            if rec.cooling_load_watt and rec.system_type == 'fcu':
                # Find smallest FCU that covers the load
                fcu = self.env["hvac.fcu"].search([
                    ('cooling_capacity_kw', '>=', rec.cooling_load_watt / 1000),
                    ('active', '=', True)
                ], order='cooling_capacity_kw asc', limit=1)
                
                # If no single FCU covers it, get the largest
                if not fcu:
                    fcu = self.env["hvac.fcu"].search([
                        ('active', '=', True)
                    ], order='cooling_capacity_kw desc', limit=1)
                
                rec.suggested_fcu_id = fcu.id if fcu else False
            else:
                rec.suggested_fcu_id = False

    @api.depends("suggested_fcu_id", "selected_fcu_id")
    def _compute_final_fcu(self):
        for rec in self:
            rec.fcu_id = rec.selected_fcu_id or rec.suggested_fcu_id

    @api.depends("cooling_load_watt", "fcu_id", "system_type")
    def _compute_suggested_fcu_qty(self):
        for rec in self:
            if rec.system_type == 'fcu' and rec.fcu_id and rec.fcu_id.cooling_capacity_kw:
                fcu_watt = rec.fcu_id.cooling_capacity_kw * 1000
                rec.suggested_fcu_qty = max(1, math.ceil(rec.cooling_load_watt / fcu_watt))
            else:
                rec.suggested_fcu_qty = 1

    @api.depends("fcu_id", "fcu_qty", "system_type")
    def _compute_fcu_subtotal(self):
        for rec in self:
            if rec.system_type == 'fcu' and rec.fcu_id:
                rec.fcu_subtotal = (rec.fcu_id.price or 0) * (rec.fcu_qty or 1)
            else:
                rec.fcu_subtotal = 0

    @api.depends("system_type", "qty")
    def _compute_thermostat_qty(self):
        for rec in self:
            rec.thermostat_qty = rec.qty or 1 if rec.system_type == 'fcu' else 0

    @api.depends("thermostat_qty", "thermostat_price")
    def _compute_thermostat_subtotal(self):
        for rec in self:
            rec.thermostat_subtotal = (rec.thermostat_price or 3000) * (rec.thermostat_qty or 0)

    @api.depends("fcu_subtotal", "thermostat_subtotal")
    def _compute_space_subtotal(self):
        for rec in self:
            rec.space_subtotal = rec.fcu_subtotal + rec.thermostat_subtotal

    # Onchange Methods
    @api.onchange("suggested_fcu_qty")
    def _onchange_suggested_fcu_qty(self):
        if self.suggested_fcu_qty and self.fcu_qty < self.suggested_fcu_qty:
            self.fcu_qty = self.suggested_fcu_qty

    @api.onchange("fcu_id")
    def _onchange_fcu_id(self):
        if self.fcu_id and self.cooling_load_watt and self.fcu_id.cooling_capacity_kw:
            fcu_watt = self.fcu_id.cooling_capacity_kw * 1000
            self.fcu_qty = max(1, math.ceil(self.cooling_load_watt / fcu_watt))

    @api.onchange("btu_per_sqm")
    def _onchange_btu_per_sqm(self):
        if self.btu_per_sqm:
            self.watt_per_sqm = self.btu_per_sqm / 3.412

    @api.onchange("system_type")
    def _onchange_system_type(self):
        self.selected_fcu_id = False
