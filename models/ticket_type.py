from odoo import models, fields, _

class TicketType(models.Model):
    _name = 'ticket.type'
    _description = 'Ticket Type'

    name = fields.Char(string="Name", required=True)
    foreign_name = fields.Char(string='Foreign Name')
    code = fields.Char(string='Code')
    serial_number = fields.Char(string='Serial Number')
    color = fields.Char(string='Color', default='#0FC640')
    icon = fields.Image(string='Icon')

    def name_get(self):
        return [(record.id, record.name) for record in self]
    