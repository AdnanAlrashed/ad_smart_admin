from odoo import models, fields, _

class TicketType(models.Model):
    _name = 'ticket.type'
    _description = 'Ticket Type'

    name = fields.Char(string=_("Name"), required=True)
    foreign_name = fields.Char(string=_('Foreign Name'))
    code = fields.Char(string=_('Code'))
    serial_number = fields.Char(string=_('Serial Number'))
    color = fields.Char(string=_('Color'), default='#0FC640')
    icon = fields.Image(string=_('Icon'))

    def name_get(self):
        return [(record.id, record.name) for record in self]
    