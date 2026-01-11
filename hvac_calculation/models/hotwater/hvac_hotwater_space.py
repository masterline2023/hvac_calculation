from odoo import models, fields, api
import math


class HVACHotWaterSpace(models.Model):
    _name = "hvac.hotwater.space"
    _description = "Hot Water Usage Point"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    
    project_id = fields.Many2one(
        "hvac.hotwater.project",
        string="Project",
        required=True,
        ondelete="cascade"
    )

    # Type
    space_type = fields.Selection([
        ('bathroom', 'Bathroom'),
        ('kitchen', 'Kitchen'),
        ('laundry', 'Laundry'),
        ('pool', 'Swimming Pool'),
        ('jacuzzi', 'Jacuzzi'),
        ('other', 'Other'),
    ], string="Type", default='bathroom')
    
    name = fields.Char(string="Name")
    qty = fields.Integer(string="Qty", default=1)

    # For Bathrooms/Kitchens - Fixture Count
    shower_count = fields.Integer(string="Showers", default=0)
    bathtub_count = fields.Integer(string="Bathtubs", default=0)
    sink_count = fields.Integer(string="Sinks", default=0)
    
    # Hot Water Demand
    demand_liters_per_day = fields.Float(string="Demand (L/day)", compute="_compute_demand", store=True, readonly=False)
    peak_flow_lpm = fields.Float(string="Peak Flow (L/min)", compute="_compute_peak_flow", store=True)

    # For Pool
    pool_length = fields.Float(string="Pool Length (m)")
    pool_width = fields.Float(string="Pool Width (m)")
    pool_depth = fields.Float(string="Pool Depth (m)", default=1.5)
    pool_area = fields.Float(string="Pool Area (m²)", compute="_compute_pool_dimensions", store=True)
    pool_volume = fields.Float(string="Pool Volume (m³)", compute="_compute_pool_dimensions", store=True)
    
    # Pool Heating
    pool_heating_load_kw = fields.Float(string="Pool Heating Load (kW)", compute="_compute_pool_heating", store=True)
    
    # Heater Selection
    suggested_heater_id = fields.Many2one("hvac.water.heater", string="Suggested Heater", compute="_compute_suggested_heater", store=True, readonly=False)
    selected_heater_id = fields.Many2one("hvac.water.heater", string="Selected Heater")
    heater_id = fields.Many2one("hvac.water.heater", string="Heater", compute="_compute_final_heater", store=True)
    heater_qty = fields.Integer(string="Heater Qty", default=1)
    heater_price = fields.Float(string="Heater Price", related="heater_id.price", readonly=True)
    heater_subtotal = fields.Float(string="Heater Subtotal", compute="_compute_heater_subtotal", store=True)
    
    # Pool Heater Selection (for pools)
    suggested_pool_heater_id = fields.Many2one("hvac.pool.heater", string="Suggested Pool Heater", compute="_compute_suggested_pool_heater", store=True, readonly=False)
    selected_pool_heater_id = fields.Many2one("hvac.pool.heater", string="Selected Pool Heater")
    pool_heater_id = fields.Many2one("hvac.pool.heater", string="Pool Heater", compute="_compute_final_pool_heater", store=True)
    pool_heater_price = fields.Float(string="Pool Heater Price", related="pool_heater_id.price", readonly=True)
    pool_heater_subtotal = fields.Float(string="Pool Heater Subtotal", compute="_compute_pool_heater_subtotal", store=True)
    
    # Space Subtotal
    space_subtotal = fields.Float(string="Space Subtotal", compute="_compute_space_subtotal", store=True)

    notes = fields.Text(string="Notes")

    # Computed Methods
    @api.depends("space_type", "shower_count", "bathtub_count", "sink_count", "qty")
    def _compute_demand(self):
        # Standard hot water demand per fixture (liters/day)
        DEMAND = {
            'shower': 50,
            'bathtub': 100,
            'sink': 20,
        }
        for rec in self:
            if rec.space_type in ('bathroom', 'kitchen', 'laundry'):
                demand = (
                    (rec.shower_count or 0) * DEMAND['shower'] +
                    (rec.bathtub_count or 0) * DEMAND['bathtub'] +
                    (rec.sink_count or 0) * DEMAND['sink']
                )
                rec.demand_liters_per_day = demand * (rec.qty or 1)
            else:
                rec.demand_liters_per_day = 0

    @api.depends("shower_count", "bathtub_count", "sink_count")
    def _compute_peak_flow(self):
        # Peak flow rates (L/min)
        FLOW = {
            'shower': 10,
            'bathtub': 15,
            'sink': 5,
        }
        for rec in self:
            rec.peak_flow_lpm = (
                (rec.shower_count or 0) * FLOW['shower'] +
                (rec.bathtub_count or 0) * FLOW['bathtub'] +
                (rec.sink_count or 0) * FLOW['sink']
            )

    @api.depends("pool_length", "pool_width", "pool_depth")
    def _compute_pool_dimensions(self):
        for rec in self:
            rec.pool_area = (rec.pool_length or 0) * (rec.pool_width or 0)
            rec.pool_volume = rec.pool_area * (rec.pool_depth or 1.5)

    @api.depends("pool_volume", "space_type")
    def _compute_pool_heating(self):
        # Pool heating load calculation
        # Approximate: 1 kW per 5 m³ for initial heating
        for rec in self:
            if rec.space_type in ('pool', 'jacuzzi') and rec.pool_volume:
                rec.pool_heating_load_kw = rec.pool_volume / 5
            else:
                rec.pool_heating_load_kw = 0

    @api.depends("demand_liters_per_day", "space_type")
    def _compute_suggested_heater(self):
        for rec in self:
            if rec.space_type not in ('pool', 'jacuzzi') and rec.demand_liters_per_day:
                # Find suitable water heater
                heater = self.env["hvac.water.heater"].search([
                    ('capacity_liters', '>=', rec.demand_liters_per_day * 0.5),  # Half daily demand as storage
                    ('active', '=', True)
                ], order='capacity_liters asc', limit=1)
                rec.suggested_heater_id = heater.id if heater else False
            else:
                rec.suggested_heater_id = False

    @api.depends("suggested_heater_id", "selected_heater_id")
    def _compute_final_heater(self):
        for rec in self:
            rec.heater_id = rec.selected_heater_id or rec.suggested_heater_id

    @api.depends("pool_heating_load_kw", "space_type", "pool_volume")
    def _compute_suggested_pool_heater(self):
        for rec in self:
            if rec.space_type in ('pool', 'jacuzzi') and rec.pool_heating_load_kw:
                heater = self.env["hvac.pool.heater"].search([
                    ('heating_capacity_kw', '>=', rec.pool_heating_load_kw),
                    ('active', '=', True)
                ], order='heating_capacity_kw asc', limit=1)
                rec.suggested_pool_heater_id = heater.id if heater else False
            else:
                rec.suggested_pool_heater_id = False

    @api.depends("suggested_pool_heater_id", "selected_pool_heater_id")
    def _compute_final_pool_heater(self):
        for rec in self:
            rec.pool_heater_id = rec.selected_pool_heater_id or rec.suggested_pool_heater_id

    @api.depends("heater_id", "heater_qty")
    def _compute_heater_subtotal(self):
        for rec in self:
            rec.heater_subtotal = (rec.heater_id.price or 0) * (rec.heater_qty or 1)

    @api.depends("pool_heater_id")
    def _compute_pool_heater_subtotal(self):
        for rec in self:
            rec.pool_heater_subtotal = rec.pool_heater_id.price or 0

    @api.depends("heater_subtotal", "pool_heater_subtotal")
    def _compute_space_subtotal(self):
        for rec in self:
            rec.space_subtotal = rec.heater_subtotal + rec.pool_heater_subtotal

    # Onchange
    @api.onchange("space_type")
    def _onchange_space_type(self):
        if self.space_type == 'bathroom':
            self.shower_count = 1
            self.sink_count = 1
        elif self.space_type == 'kitchen':
            self.sink_count = 1
        else:
            self.shower_count = 0
            self.bathtub_count = 0
            self.sink_count = 0
