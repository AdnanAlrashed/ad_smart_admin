from odoo import fields, models, api, _

class TicketStatus(models.Model):
    _name = 'ticket.status'
    _description = 'for ticket status'
    