from odoo import models, fields, api
from odoo.exceptions import UserError


class HVACCoolingProject(models.Model):
    _name = "hvac.cooling.project"
    _description = "Central Air Conditioning Project"
    _order = "date desc, id desc"

    name = fields.Char(string="Project Name", required=True)
    customer_id = fields.Many2one("res.partner", string="Customer")
    attention_to = fields.Char(string="Attention To")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    
    offer_code = fields.Char(string="Offer Code", readonly=True, copy=False, default="New")
    
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', readonly=True)

    # Spaces
    space_ids = fields.One2many("hvac.cooling.space", "project_id", string="Spaces")

    # Cooling Load Totals
    total_cooling_load_watt = fields.Float(string="Total Cooling Load (W)", compute="_compute_totals", store=True)
    total_cooling_load_kw = fields.Float(string="Total Cooling Load (kW)", compute="_compute_totals", store=True)
    total_cooling_load_btu = fields.Float(string="Total Cooling Load (BTU/hr)", compute="_compute_totals", store=True)
    total_cooling_load_ton = fields.Float(string="Total Cooling Load (TR)", compute="_compute_totals", store=True)
    total_cooling_area = fields.Float(string="Total Cooling Area (m²)", compute="_compute_totals", store=True)

    # Chiller Selection
    suggested_chiller_id = fields.Many2one("hvac.chiller", string="Suggested Chiller", compute="_compute_suggested_chiller", store=True, readonly=False)
    selected_chiller_id = fields.Many2one("hvac.chiller", string="Selected Chiller")
    chiller_id = fields.Many2one("hvac.chiller", string="Chiller", compute="_compute_final_chiller", store=True)
    chiller_qty = fields.Integer(string="Chiller Qty", default=1)
    chiller_price = fields.Float(string="Chiller Price", compute="_compute_equipment_totals", store=True)

    # AHU Selection (Optional)
    ahu_ids = fields.Many2many("hvac.ahu", string="AHUs")
    ahu_total = fields.Float(string="AHU Total", compute="_compute_equipment_totals", store=True)

    # Ductwork
    duct_line_ids = fields.One2many("hvac.duct.line", "project_id", string="Ductwork & Diffusers")
    ductwork_total = fields.Float(string="Ductwork Total", compute="_compute_ductwork_total", store=True)

    # Pricing
    fcu_total = fields.Float(string="FCU Total", compute="_compute_equipment_totals", store=True)
    thermostat_total = fields.Float(string="Thermostat Total", compute="_compute_equipment_totals", store=True)
    thermostat_count = fields.Integer(string="Thermostat Count", compute="_compute_equipment_totals", store=True)
    equipment_subtotal = fields.Float(string="Equipment Subtotal", compute="_compute_equipment_totals", store=True)
    equipment_discount = fields.Float(string="Equipment Discount (%)", default=0)
    equipment_total = fields.Float(string="Equipment Total", compute="_compute_equipment_totals", store=True)
    ductwork_discount = fields.Float(string="Ductwork Discount (%)", default=0)
    ductwork_total_after_discount = fields.Float(string="Ductwork After Discount", compute="_compute_ductwork_total", store=True)
    grand_total = fields.Float(string="Grand Total", compute="_compute_grand_total", store=True)

    # Terms
    terms_template_id = fields.Many2one("hvac.terms", string="Terms Template", domain=[('active', '=', True), ('apply_cooling', '=', True)])
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
                vals['offer_code'] = self.env['ir.sequence'].next_by_code('hvac.cooling.project') or 'New'
        return super().create(vals_list)

    @api.depends("space_ids.cooling_load_watt", "space_ids.cooling_load_btu", "space_ids.cooling_load_ton", "space_ids.area")
    def _compute_totals(self):
        for rec in self:
            rec.total_cooling_load_watt = sum(rec.space_ids.mapped("cooling_load_watt"))
            rec.total_cooling_load_kw = rec.total_cooling_load_watt / 1000
            rec.total_cooling_load_btu = sum(rec.space_ids.mapped("cooling_load_btu"))
            rec.total_cooling_load_ton = sum(rec.space_ids.mapped("cooling_load_ton"))
            rec.total_cooling_area = sum(rec.space_ids.mapped("area"))

    @api.depends("total_cooling_load_kw")
    def _compute_suggested_chiller(self):
        for rec in self:
            if rec.total_cooling_load_kw:
                chiller = self.env["hvac.chiller"].search([
                    ('cooling_capacity_kw', '>=', rec.total_cooling_load_kw), ('active', '=', True)
                ], order='cooling_capacity_kw asc', limit=1)
                rec.suggested_chiller_id = chiller.id if chiller else False
            else:
                rec.suggested_chiller_id = False

    @api.depends("suggested_chiller_id", "selected_chiller_id")
    def _compute_final_chiller(self):
        for rec in self:
            rec.chiller_id = rec.selected_chiller_id or rec.suggested_chiller_id

    @api.depends("chiller_id", "chiller_qty", "ahu_ids", "space_ids.fcu_subtotal", "space_ids.thermostat_subtotal", "equipment_discount")
    def _compute_equipment_totals(self):
        for rec in self:
            rec.chiller_price = (rec.chiller_id.price or 0) * (rec.chiller_qty or 1)
            rec.ahu_total = sum(rec.ahu_ids.mapped("price"))
            rec.fcu_total = sum(rec.space_ids.mapped("fcu_subtotal"))
            rec.thermostat_count = sum(rec.space_ids.mapped("thermostat_qty"))
            rec.thermostat_total = sum(rec.space_ids.mapped("thermostat_subtotal"))
            rec.equipment_subtotal = rec.chiller_price + rec.ahu_total + rec.fcu_total + rec.thermostat_total
            discount = rec.equipment_discount or 0
            rec.equipment_total = rec.equipment_subtotal * (1 - discount / 100)

    @api.depends("duct_line_ids.subtotal", "ductwork_discount")
    def _compute_ductwork_total(self):
        for rec in self:
            rec.ductwork_total = sum(rec.duct_line_ids.mapped("subtotal"))
            discount = rec.ductwork_discount or 0
            rec.ductwork_total_after_discount = rec.ductwork_total * (1 - discount / 100)

    @api.depends("equipment_total", "ductwork_total_after_discount")
    def _compute_grand_total(self):
        for rec in self:
            rec.grand_total = rec.equipment_total + rec.ductwork_total_after_discount

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
        
        if self.chiller_id:
            order_lines.append((0, 0, {
                "name": f"{self.chiller_id.name} ({self.chiller_id.cooling_capacity_ton:.1f} TR)",
                "product_uom_qty": self.chiller_qty or 1,
                "price_unit": self.chiller_id.price or 0,
            }))
        
        for ahu in self.ahu_ids:
            order_lines.append((0, 0, {
                "name": f"{ahu.name} ({ahu.airflow_cfm:.0f} CFM)",
                "product_uom_qty": 1,
                "price_unit": ahu.price or 0,
            }))
        
        for space in self.space_ids.filtered(lambda s: s.system_type == 'fcu' and s.fcu_id):
            order_lines.append((0, 0, {
                "name": f"{space.fcu_id.name} - {space.room_name or 'Room'}",
                "product_uom_qty": space.fcu_qty or 1,
                "price_unit": space.fcu_id.price or 0,
            }))
            if space.thermostat_qty:
                order_lines.append((0, 0, {
                    "name": f"Thermostat - {space.room_name or 'Room'}",
                    "product_uom_qty": space.thermostat_qty,
                    "price_unit": space.thermostat_price or 3000,
                }))
        
        for line in self.duct_line_ids:
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
