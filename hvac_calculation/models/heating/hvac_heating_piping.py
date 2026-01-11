from odoo import models, fields, api


class HVACHeatingPipingMaterial(models.Model):
    _name = "hvac.heating.piping.material"
    _description = "Heating Piping Material"
    _order = "name"

    name = fields.Char(string="Material Name", required=True)
    
    material_type = fields.Selection([
        ('ppr', 'PPR Pipe'),
        ('pex', 'PEX Pipe'),
        ('copper', 'Copper Pipe'),
        ('steel', 'Steel Pipe'),
        ('multilayer', 'Multilayer Pipe'),
    ], string="Type", default='ppr')
    
    diameter = fields.Float(string="Diameter (mm)")
    unit = fields.Selection([
        ('meter', 'Meter'),
        ('piece', 'Piece'),
        ('set', 'Set'),
    ], string="Unit", default='meter')
    
    price_per_unit = fields.Float(string="Price per Unit", required=True)
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")


class HVACHeatingPipingLine(models.Model):
    _name = "hvac.heating.piping.line"
    _description = "Heating Piping Line"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    
    project_id = fields.Many2one(
        "hvac.heating.project",
        string="Project",
        required=True,
        ondelete="cascade"
    )
    
    name = fields.Char(string="Description", required=True)
    material_id = fields.Many2one("hvac.heating.piping.material", string="Material")
    
    unit = fields.Selection([
        ('Meter', 'Meter'),
        ('No.', 'Piece'),
        ('Set', 'Set'),
        ('Lot', 'Lot'),
    ], string="Unit", default='Meter')
    
    quantity = fields.Float(string="Quantity", default=1)
    unit_price = fields.Float(string="Unit Price")
    
    subtotal = fields.Float(
        string="Subtotal",
        compute="_compute_subtotal",
        store=True
    )
    
    notes = fields.Text(string="Notes")

    @api.depends("quantity", "unit_price")
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = (rec.quantity or 0) * (rec.unit_price or 0)

    @api.onchange("material_id")
    def _onchange_material_id(self):
        if self.material_id:
            self.name = self.material_id.name
            self.unit_price = self.material_id.price_per_unit
