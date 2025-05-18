from odoo import models, fields,_

CODE_PRIORITY = [
    (_('high'), _("عاليه")),
    (_('medium'), _("متوسطه")),
    (_('low'), _("منخفضه")),
    (_('other'), _("اخرى")),
]

class Priority(models.Model):
    _name = 'priority'
    _description = 'Priority Model'

    name = fields.Char(string=_("Name"), required=True, default="")
    foreign_name = fields.Char(string=_("Foreign Name"), default="", required=False)
    code = fields.Selection(
        selection=CODE_PRIORITY,
        string=_("Code"),
        copy=False, index=True,
        tracking=3,
        default='low')
    is_default = fields.Boolean(string=_("Is Default"))
    color = fields.Char(string=_("Color"), default="#0FC640")
    icon_priority = fields.Image(string=_("Icon Priority"))

    def name_get(self):
        return [(record.id, record.name) for record in self]