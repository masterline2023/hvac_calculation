from odoo import models, fields, api
import math


class HVACHeatingSpace(models.Model):
    _name = "hvac.heating.space"
    _description = "Heating Space/Room"
    _order = "floor_sequence, sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    
    project_id = fields.Many2one(
        "hvac.heating.project",
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
    
    floor_sequence = fields.Integer(
        string="Floor Sequence",
        compute="_compute_floor_sequence",
        store=True
    )
    
    room_name = fields.Char(string="Room Name")
    is_bathroom = fields.Boolean(string="Bathroom", default=False)

    # Dimensions
    area = fields.Float(string="Area (m²)")
    
    # Heat Load
    watt_per_sqm = fields.Float(string="Watt / m²", default=100)
    load_factor_percent = fields.Float(string="Load Factor (%)", default=100)
    qty = fields.Integer(string="Room Qty", default=1)
    heat_load = fields.Float(string="Heat Load (W)", compute="_compute_heat_load", store=True)

    # System Type
    system_type = fields.Selection([
        ('ufh', 'Under Floor Heating'),
        ('radiator', 'Radiator'),
    ], string="System Type", default='radiator')
    
    # Radiator Selection
    preferred_height = fields.Selection([
        ('580', '580 mm'),
        ('680', '680 mm'),
        ('880', '880 mm'),
    ], string="Preferred Height", default='680')

    suggested_radiator_id = fields.Many2one(
        "hvac.radiator", string="Suggested Radiator",
        compute="_compute_suggested_radiator", store=True, readonly=False
    )
    selected_radiator_id = fields.Many2one("hvac.radiator", string="Selected Radiator")
    radiator_id = fields.Many2one("hvac.radiator", string="Radiator", compute="_compute_final_radiator", store=True)
    
    radiator_size = fields.Char(string="Radiator Size", related="radiator_id.size_display", readonly=True)
    radiator_output = fields.Float(string="Radiator Output (W)", related="radiator_id.watt_output", readonly=True)
    
    suggested_radiator_qty = fields.Integer(string="Suggested Qty", compute="_compute_suggested_radiator_qty", store=True)
    radiator_qty = fields.Integer(string="Radiator Qty", default=1)
    radiator_unit_price = fields.Float(string="Radiator Unit Price", related="radiator_id.price", readonly=True)
    radiator_subtotal = fields.Float(string="Radiator Subtotal", compute="_compute_radiator_subtotal", store=True)

    # UFH
    ufh_price_per_sqm = fields.Float(string="UFH Price/m²", default=1500)
    ufh_subtotal = fields.Float(string="UFH Subtotal", compute="_compute_ufh_subtotal", store=True)
    
    # Thermostat
    thermostat_price = fields.Float(string="Thermostat Price", default=5000)
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

    @api.depends("area", "watt_per_sqm", "load_factor_percent", "qty")
    def _compute_heat_load(self):
        for rec in self:
            load_factor = (rec.load_factor_percent or 100) / 100
            rec.heat_load = (rec.area or 0) * (rec.watt_per_sqm or 100) * load_factor * (rec.qty or 1)

    @api.depends("heat_load", "system_type", "is_bathroom", "preferred_height")
    def _compute_suggested_radiator(self):
        for rec in self:
            if rec.heat_load and rec.system_type == 'radiator':
                if rec.is_bathroom:
                    largest = self.env["hvac.radiator"].search([
                        ('radiator_type', '=', 'towel'), ('active', '=', True)
                    ], order='watt_output desc', limit=1)
                    if largest and rec.heat_load <= largest.watt_output:
                        radiator = self.env["hvac.radiator"].search([
                            ('watt_output', '>=', rec.heat_load),
                            ('radiator_type', '=', 'towel'), ('active', '=', True)
                        ], order='watt_output asc', limit=1)
                    else:
                        radiator = largest
                else:
                    preferred_h = int(rec.preferred_height or 680)
                    largest = self.env["hvac.radiator"].search([
                        ('radiator_type', '=', 'aluminum'),
                        ('height', '=', preferred_h), ('active', '=', True)
                    ], order='watt_output desc', limit=1)
                    if largest and rec.heat_load <= largest.watt_output:
                        radiator = self.env["hvac.radiator"].search([
                            ('watt_output', '>=', rec.heat_load),
                            ('radiator_type', '=', 'aluminum'),
                            ('height', '=', preferred_h), ('active', '=', True)
                        ], order='watt_output asc', limit=1)
                    else:
                        radiator = largest
                    if not radiator:
                        radiator = self.env["hvac.radiator"].search([
                            ('radiator_type', '=', 'aluminum'), ('active', '=', True)
                        ], order='watt_output desc', limit=1)
                rec.suggested_radiator_id = radiator.id if radiator else False
            else:
                rec.suggested_radiator_id = False

    @api.depends("suggested_radiator_id", "selected_radiator_id")
    def _compute_final_radiator(self):
        for rec in self:
            rec.radiator_id = rec.selected_radiator_id or rec.suggested_radiator_id

    @api.depends("heat_load", "radiator_id", "system_type")
    def _compute_suggested_radiator_qty(self):
        for rec in self:
            if rec.system_type == 'radiator' and rec.radiator_id and rec.radiator_id.watt_output:
                rec.suggested_radiator_qty = max(1, math.ceil(rec.heat_load / rec.radiator_id.watt_output))
            else:
                rec.suggested_radiator_qty = 1

    @api.depends("radiator_id", "radiator_qty", "system_type")
    def _compute_radiator_subtotal(self):
        for rec in self:
            if rec.system_type == 'radiator' and rec.radiator_id:
                rec.radiator_subtotal = (rec.radiator_id.price or 0) * (rec.radiator_qty or 1)
            else:
                rec.radiator_subtotal = 0

    @api.depends("area", "ufh_price_per_sqm", "system_type")
    def _compute_ufh_subtotal(self):
        for rec in self:
            if rec.system_type == 'ufh':
                rec.ufh_subtotal = (rec.area or 0) * (rec.ufh_price_per_sqm or 1500)
            else:
                rec.ufh_subtotal = 0

    @api.depends("system_type", "qty")
    def _compute_thermostat_qty(self):
        for rec in self:
            rec.thermostat_qty = rec.qty or 1 if rec.system_type == 'ufh' else 0

    @api.depends("system_type", "thermostat_qty", "thermostat_price")
    def _compute_thermostat_subtotal(self):
        for rec in self:
            if rec.system_type == 'ufh' and rec.thermostat_qty:
                rec.thermostat_subtotal = (rec.thermostat_price or 5000) * rec.thermostat_qty
            else:
                rec.thermostat_subtotal = 0

    @api.depends("radiator_subtotal", "ufh_subtotal", "thermostat_subtotal", "system_type")
    def _compute_space_subtotal(self):
        for rec in self:
            if rec.system_type == 'radiator':
                rec.space_subtotal = rec.radiator_subtotal
            elif rec.system_type == 'ufh':
                rec.space_subtotal = rec.ufh_subtotal + rec.thermostat_subtotal
            else:
                rec.space_subtotal = 0

    # Onchange Methods
    @api.onchange("suggested_radiator_qty")
    def _onchange_suggested_radiator_qty(self):
        if self.suggested_radiator_qty and self.radiator_qty < self.suggested_radiator_qty:
            self.radiator_qty = self.suggested_radiator_qty

    @api.onchange("radiator_id")
    def _onchange_radiator_id(self):
        if self.radiator_id and self.heat_load and self.radiator_id.watt_output:
            self.radiator_qty = max(1, math.ceil(self.heat_load / self.radiator_id.watt_output))

    @api.onchange("preferred_height")
    def _onchange_preferred_height(self):
        if self.system_type == 'radiator' and not self.is_bathroom and self.heat_load:
            self.selected_radiator_id = False
            preferred_h = int(self.preferred_height or 680)
            largest = self.env["hvac.radiator"].search([
                ('radiator_type', '=', 'aluminum'),
                ('height', '=', preferred_h), ('active', '=', True)
            ], order='watt_output desc', limit=1)
            if largest:
                if self.heat_load <= largest.watt_output:
                    radiator = self.env["hvac.radiator"].search([
                        ('watt_output', '>=', self.heat_load),
                        ('radiator_type', '=', 'aluminum'),
                        ('height', '=', preferred_h), ('active', '=', True)
                    ], order='watt_output asc', limit=1)
                else:
                    radiator = largest
                if radiator:
                    self.suggested_radiator_id = radiator.id
                    self.radiator_qty = max(1, math.ceil(self.heat_load / radiator.watt_output))

    @api.onchange("system_type")
    def _onchange_system_type(self):
        self.selected_radiator_id = False
        if self.system_type == 'ufh':
            self.watt_per_sqm = 80
            self.ufh_price_per_sqm = 1500
        else:
            self.watt_per_sqm = 100

    @api.onchange("is_bathroom")
    def _onchange_is_bathroom(self):
        self.selected_radiator_id = False

    @api.onchange("area", "ufh_price_per_sqm")
    def _onchange_ufh_fields(self):
        if self.system_type == 'ufh':
            self.ufh_subtotal = (self.area or 0) * (self.ufh_price_per_sqm or 1500)
