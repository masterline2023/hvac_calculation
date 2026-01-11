from odoo import models, fields, api
from odoo.exceptions import UserError


class HVACHotWaterProject(models.Model):
    _name = "hvac.hotwater.project"
    _description = "Hot Water & Pool Heating Project"
    _order = "date desc, id desc"

    name = fields.Char(string="Project Name", required=True)
    customer_id = fields.Many2one("res.partner", string="Customer")
    attention_to = fields.Char(string="Attention To")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    
    offer_code = fields.Char(string="Offer Code", readonly=True, copy=False, default="New")
    
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', readonly=True)

    # Spaces / Usage Points
    space_ids = fields.One2many("hvac.hotwater.space", "project_id", string="Usage Points")

    # Totals
    total_demand_liters = fields.Float(string="Total Daily Demand (L)", compute="_compute_totals", store=True)
    total_peak_flow = fields.Float(string="Total Peak Flow (L/min)", compute="_compute_totals", store=True)
    total_pool_volume = fields.Float(string="Total Pool Volume (m³)", compute="_compute_totals", store=True)
    total_pool_heating_kw = fields.Float(string="Total Pool Heating (kW)", compute="_compute_totals", store=True)

    # Additional Equipment
    equipment_line_ids = fields.One2many("hvac.hotwater.equipment.line", "project_id", string="Additional Equipment")
    equipment_line_total = fields.Float(string="Additional Equipment Total", compute="_compute_equipment_line_total", store=True)

    # Pricing
    heater_total = fields.Float(string="Water Heater Total", compute="_compute_equipment_totals", store=True)
    pool_heater_total = fields.Float(string="Pool Heater Total", compute="_compute_equipment_totals", store=True)
    equipment_subtotal = fields.Float(string="Equipment Subtotal", compute="_compute_equipment_totals", store=True)
    equipment_discount = fields.Float(string="Equipment Discount (%)", default=0)
    equipment_total = fields.Float(string="Equipment Total", compute="_compute_equipment_totals", store=True)
    grand_total = fields.Float(string="Grand Total", compute="_compute_grand_total", store=True)

    # Terms
    terms_template_id = fields.Many2one("hvac.terms", string="Terms Template", domain=[('active', '=', True), ('apply_hotwater', '=', True)])
    offer_includes = fields.Html(string="The Offer Includes")
    offer_excludes = fields.Html(string="The Offer Doesn't Include")
    payment_terms = fields.Html(string="Payment Terms")
    execution_time = fields.Html(string="Execution Time")
    warranty = fields.Html(string="Warranty")
    validity_days = fields.Integer(string="Offer Validity (Days)", default=7)
    additional_notes = fields.Html(string="Additional Notes")

    # Sale Order
    sale_order_id = fields.Many2one("sale.order", string="Quotation", readonly=True, copy=False)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('quoted', 'Quotation Created'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft')

    # Computed Methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('offer_code', 'New') == 'New':
                vals['offer_code'] = self.env['ir.sequence'].next_by_code('hvac.hotwater.project') or 'New'
        return super().create(vals_list)

    @api.depends("space_ids.demand_liters_per_day", "space_ids.peak_flow_lpm", "space_ids.pool_volume", "space_ids.pool_heating_load_kw")
    def _compute_totals(self):
        for rec in self:
            rec.total_demand_liters = sum(rec.space_ids.mapped("demand_liters_per_day"))
            rec.total_peak_flow = sum(rec.space_ids.mapped("peak_flow_lpm"))
            rec.total_pool_volume = sum(rec.space_ids.filtered(lambda s: s.space_type in ('pool', 'jacuzzi')).mapped("pool_volume"))
            rec.total_pool_heating_kw = sum(rec.space_ids.mapped("pool_heating_load_kw"))

    @api.depends("space_ids.heater_subtotal", "space_ids.pool_heater_subtotal", "equipment_line_total", "equipment_discount")
    def _compute_equipment_totals(self):
        for rec in self:
            rec.heater_total = sum(rec.space_ids.mapped("heater_subtotal"))
            rec.pool_heater_total = sum(rec.space_ids.mapped("pool_heater_subtotal"))
            rec.equipment_subtotal = rec.heater_total + rec.pool_heater_total + rec.equipment_line_total
            discount = rec.equipment_discount or 0
            rec.equipment_total = rec.equipment_subtotal * (1 - discount / 100)

    @api.depends("equipment_line_ids.subtotal")
    def _compute_equipment_line_total(self):
        for rec in self:
            rec.equipment_line_total = sum(rec.equipment_line_ids.mapped("subtotal"))

    @api.depends("equipment_total")
    def _compute_grand_total(self):
        for rec in self:
            rec.grand_total = rec.equipment_total

    @api.onchange("terms_template_id")
    def _onchange_terms_template(self):
        if self.terms_template_id:
            t = self.terms_template_id
            self.offer_includes = t.offer_includes
            self.offer_excludes = t.offer_excludes
            self.payment_terms = t.payment_terms
            self.execution_time = t.execution_time
            self.warranty = t.warranty
            self.additional_notes = t.additional_notes

    # Actions
    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_create_quotation(self):
        self.ensure_one()
        if not self.customer_id:
            raise UserError("Please select a customer first.")
        
        order_lines = []
        
        for space in self.space_ids:
            if space.heater_id:
                order_lines.append((0, 0, {
                    "name": f"{space.heater_id.name} - {space.name or space.space_type}",
                    "product_uom_qty": space.heater_qty or 1,
                    "price_unit": space.heater_id.price or 0,
                }))
            if space.pool_heater_id:
                order_lines.append((0, 0, {
                    "name": f"{space.pool_heater_id.name} - {space.name or 'Pool'}",
                    "product_uom_qty": 1,
                    "price_unit": space.pool_heater_id.price or 0,
                }))
        
        for line in self.equipment_line_ids:
            order_lines.append((0, 0, {
                "name": line.name,
                "product_uom_qty": line.quantity or 1,
                "price_unit": line.unit_price or 0,
            }))
        
        sale_order = self.env['sale.order'].create({
            'partner_id': self.customer_id.id,
            'origin': self.offer_code,
            'order_line': order_lines,
        })
        
        self.write({'sale_order_id': sale_order.id, 'state': 'quoted'})
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_quotation(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_done(self):
        self.write({'state': 'done'})


class HVACHotWaterEquipmentLine(models.Model):
    _name = "hvac.hotwater.equipment.line"
    _description = "Hot Water Equipment Line"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    
    project_id = fields.Many2one(
        "hvac.hotwater.project",
        string="Project",
        required=True,
        ondelete="cascade"
    )
    
    name = fields.Char(string="Description", required=True)
    equipment_id = fields.Many2one("hvac.pool.equipment", string="Equipment")
    
    unit = fields.Selection([
        ('No.', 'Piece'),
        ('Set', 'Set'),
        ('Meter', 'Meter'),
    ], string="Unit", default='No.')
    
    quantity = fields.Float(string="Quantity", default=1)
    unit_price = fields.Float(string="Unit Price")
    
    subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal", store=True)
    
    notes = fields.Text(string="Notes")

    @api.depends("quantity", "unit_price")
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = (rec.quantity or 0) * (rec.unit_price or 0)

    @api.onchange("equipment_id")
    def _onchange_equipment_id(self):
        if self.equipment_id:
            self.name = self.equipment_id.name
            self.unit_price = self.equipment_id.price
