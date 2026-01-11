from odoo import models, fields, api


class HVACDuctMaterial(models.Model):
    _name = "hvac.duct.material"
    _description = "Ductwork Material"
    _order = "name"

    name = fields.Char(string="Material Name", required=True)
    
    material_type = fields.Selection([
        ('gi', 'Galvanized Iron'),
        ('aluminum', 'Aluminum'),
        ('flexible', 'Flexible Duct'),
        ('fabric', 'Fabric Duct'),
        ('fiberglass', 'Fiberglass'),
    ], string="Type", default='gi')
    
    thickness = fields.Float(string="Thickness (mm)")
    insulation = fields.Boolean(string="Insulated", default=True)
    insulation_thickness = fields.Float(string="Insulation Thickness (mm)", default=25)
    
    unit = fields.Selection([
        ('kg', 'Kilogram'),
        ('sqm', 'Square Meter'),
        ('meter', 'Linear Meter'),
    ], string="Unit", default='kg')
    
    price_per_unit = fields.Float(string="Price per Unit", required=True)
    
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")


class HVACDiffuser(models.Model):
    _name = "hvac.diffuser"
    _description = "HVAC Diffuser/Grille"
    _order = "airflow_cfm asc"

    name = fields.Char(string="Diffuser Name", required=True)
    
    diffuser_type = fields.Selection([
        ('supply_square', 'Supply - Square'),
        ('supply_round', 'Supply - Round'),
        ('supply_linear', 'Supply - Linear'),
        ('supply_jet', 'Supply - Jet'),
        ('return_square', 'Return - Square'),
        ('return_round', 'Return - Round'),
        ('return_egg_crate', 'Return - Egg Crate'),
        ('exhaust', 'Exhaust Grille'),
    ], string="Type", default='supply_square')
    
    size = fields.Char(string="Size")
    airflow_cfm = fields.Float(string="Airflow (CFM)")
    
    material = fields.Selection([
        ('aluminum', 'Aluminum'),
        ('steel', 'Steel'),
        ('plastic', 'Plastic'),
    ], string="Material", default='aluminum')
    
    price = fields.Float(string="Price", required=True)
    
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")

    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            if rec.size:
                name += f" ({rec.size})"
            if rec.airflow_cfm:
                name += f" - {rec.airflow_cfm:.0f} CFM"
            result.append((rec.id, name))
        return result


class HVACDuctLine(models.Model):
    _name = "hvac.duct.line"
    _description = "Ductwork Line"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    
    project_id = fields.Many2one(
        "hvac.cooling.project",
        string="Project",
        required=True,
        ondelete="cascade"
    )
    
    name = fields.Char(string="Description", required=True)
    
    line_type = fields.Selection([
        ('duct', 'Ductwork'),
        ('diffuser', 'Diffuser/Grille'),
        ('accessory', 'Accessory'),
        ('insulation', 'Insulation'),
    ], string="Type", default='duct')
    
    material_id = fields.Many2one("hvac.duct.material", string="Material")
    diffuser_id = fields.Many2one("hvac.diffuser", string="Diffuser")
    
    unit = fields.Selection([
        ('kg', 'Kilogram'),
        ('sqm', 'Square Meter'),
        ('meter', 'Linear Meter'),
        ('No.', 'Piece'),
        ('Set', 'Set'),
    ], string="Unit", default='kg')
    
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

    @api.onchange("diffuser_id")
    def _onchange_diffuser_id(self):
        if self.diffuser_id:
            self.name = self.diffuser_id.name
            self.unit_price = self.diffuser_id.price
            self.unit = 'No.'
