from odoo import models, fields,_

CODE_PRIORITY = [
    ('high', "عاليه"),
    ('medium', "متوسطه"),
    ('low', "منخفضه"),
    ('other', "اخرى"),
]

class Priority(models.Model):
    _name = 'priority'
    _description = 'Priority Model'

    name = fields.Char(string="Name", required=True, default="")
    foreign_name = fields.Char(string="Foreign Name", default="", required=False)
    code = fields.Selection(
        selection=CODE_PRIORITY,
        string="Code",
        copy=False, index=True,
        tracking=3,
        default='low')
    is_default = fields.Boolean(string="Is Default")
    color = fields.Char(string="Color", default="#0FC640")
    icon_priority = fields.Image(string="Icon Priority")

    def name_get(self):
        return [(record.id, record.name) for record in self]