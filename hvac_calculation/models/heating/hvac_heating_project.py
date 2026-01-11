from odoo import models, fields, api
from odoo.exceptions import UserError


class HVACHeatingProject(models.Model):
    _name = "hvac.heating.project"
    _description = "Central Heating Project"
    _order = "date desc, id desc"

    name = fields.Char(string="Project Name", required=True)
    customer_id = fields.Many2one("res.partner", string="Customer")
    attention_to = fields.Char(string="Attention To")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    
    offer_code = fields.Char(string="Offer Code", readonly=True, copy=False, default="New")
    
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', readonly=True)

    # Spaces
    space_ids = fields.One2many("hvac.heating.space", "project_id", string="Spaces")

    # Heat Load
    total_heat_load = fields.Float(string="Total Heat Load (W)", compute="_compute_totals", store=True)
    total_heat_load_kw = fields.Float(string="Total Heat Load (kW)", compute="_compute_totals", store=True)
    total_heating_area = fields.Float(string="Total Heating Area (m²)", compute="_compute_totals", store=True)

    # Boiler Selection
    suggested_boiler_id = fields.Many2one("hvac.boiler", string="Suggested Boiler", compute="_compute_suggested_boiler", store=True, readonly=False)
    selected_boiler_id = fields.Many2one("hvac.boiler", string="Selected Boiler")
    boiler_id = fields.Many2one("hvac.boiler", string="Boiler", compute="_compute_final_boiler", store=True)
    boiler_qty = fields.Integer(string="Boiler Qty", default=1)
    boiler_price = fields.Float(string="Boiler Price", compute="_compute_equipment_totals", store=True)

    # Piping
    piping_line_ids = fields.One2many("hvac.heating.piping.line", "project_id", string="Piping Network")
    piping_total = fields.Float(string="Piping Total", compute="_compute_piping_total", store=True)

    # Pricing
    ufh_total = fields.Float(string="UFH Total", compute="_compute_equipment_totals", store=True)
    thermostat_total = fields.Float(string="Thermostat Total", compute="_compute_equipment_totals", store=True)
    thermostat_count = fields.Integer(string="Thermostat Count", compute="_compute_equipment_totals", store=True)
    equipment_subtotal = fields.Float(string="Equipment Subtotal", compute="_compute_equipment_totals", store=True)
    equipment_discount = fields.Float(string="Equipment Discount (%)", default=0)
    equipment_total = fields.Float(string="Equipment Total", compute="_compute_equipment_totals", store=True)
    piping_discount = fields.Float(string="Piping Discount (%)", default=0)
    piping_total_after_discount = fields.Float(string="Piping After Discount", compute="_compute_piping_total", store=True)
    grand_total = fields.Float(string="Grand Total", compute="_compute_grand_total", store=True)

    # Terms
    terms_template_id = fields.Many2one("hvac.terms", string="Terms Template", domain=[('active', '=', True), ('apply_heating', '=', True)])
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
                vals['offer_code'] = self.env['ir.sequence'].next_by_code('hvac.heating.project') or 'New'
        return super().create(vals_list)

    @api.depends("space_ids.heat_load", "space_ids.area")
    def _compute_totals(self):
        for rec in self:
            rec.total_heat_load = sum(rec.space_ids.mapped("heat_load"))
            rec.total_heat_load_kw = rec.total_heat_load / 1000
            rec.total_heating_area = sum(rec.space_ids.mapped("area"))

    @api.depends("total_heat_load_kw")
    def _compute_suggested_boiler(self):
        for rec in self:
            if rec.total_heat_load_kw:
                boiler = self.env["hvac.boiler"].search([
                    ('kw_output', '>=', rec.total_heat_load_kw), ('active', '=', True)
                ], order='kw_output asc', limit=1)
                rec.suggested_boiler_id = boiler.id if boiler else False
            else:
                rec.suggested_boiler_id = False

    @api.depends("suggested_boiler_id", "selected_boiler_id")
    def _compute_final_boiler(self):
        for rec in self:
            rec.boiler_id = rec.selected_boiler_id or rec.suggested_boiler_id

    @api.depends("boiler_id", "boiler_qty", "space_ids.radiator_subtotal", "space_ids.ufh_subtotal", "space_ids.thermostat_subtotal", "equipment_discount")
    def _compute_equipment_totals(self):
        for rec in self:
            rec.boiler_price = (rec.boiler_id.price or 0) * (rec.boiler_qty or 1)
            radiators_total = sum(rec.space_ids.mapped("radiator_subtotal"))
            rec.ufh_total = sum(rec.space_ids.mapped("ufh_subtotal"))
            rec.thermostat_count = sum(rec.space_ids.mapped("thermostat_qty"))
            rec.thermostat_total = sum(rec.space_ids.mapped("thermostat_subtotal"))
            rec.equipment_subtotal = rec.boiler_price + radiators_total + rec.ufh_total + rec.thermostat_total
            discount = rec.equipment_discount or 0
            rec.equipment_total = rec.equipment_subtotal * (1 - discount / 100)

    @api.depends("piping_line_ids.subtotal", "piping_discount")
    def _compute_piping_total(self):
        for rec in self:
            rec.piping_total = sum(rec.piping_line_ids.mapped("subtotal"))
            discount = rec.piping_discount or 0
            rec.piping_total_after_discount = rec.piping_total * (1 - discount / 100)

    @api.depends("equipment_total", "piping_total_after_discount")
    def _compute_grand_total(self):
        for rec in self:
            rec.grand_total = rec.equipment_total + rec.piping_total_after_discount

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
        
        if self.boiler_id:
            order_lines.append((0, 0, {
                "name": f"{self.boiler_id.name} ({self.boiler_id.kw_output} kW)",
                "product_uom_qty": self.boiler_qty or 1,
                "price_unit": self.boiler_id.price or 0,
            }))
        
        for space in self.space_ids.filtered(lambda s: s.system_type == 'radiator' and s.radiator_id):
            order_lines.append((0, 0, {
                "name": f"{space.radiator_id.name} - {space.room_name or 'Room'}",
                "product_uom_qty": space.radiator_qty or 1,
                "price_unit": space.radiator_id.price or 0,
            }))
        
        for space in self.space_ids.filtered(lambda s: s.system_type == 'ufh'):
            order_lines.append((0, 0, {
                "name": f"Under Floor Heating - {space.room_name or 'Room'}",
                "product_uom_qty": space.area or 1,
                "price_unit": space.ufh_price_per_sqm or 1500,
            }))
            if space.thermostat_qty:
                order_lines.append((0, 0, {
                    "name": f"Room Thermostat - {space.room_name or 'Room'}",
                    "product_uom_qty": space.thermostat_qty,
                    "price_unit": space.thermostat_price or 5000,
                }))
        
        for line in self.piping_line_ids:
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
