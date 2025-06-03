from odoo import models, fields, api

class TicketReferral(models.Model):
    _name = 'ticket.referral'
    _description = 'سجل إحالات التذاكر'
    _order = 'create_date desc'
    
    ticket_id = fields.Many2one(
        'ticket',
        string='التذكرة',
        required=True
    )
    from_department_id = fields.Many2one(
        'hr.department',
        string='القسم المرسل',
        required=True
    )
    to_department_id = fields.Many2one(
        'hr.department',
        string='القسم المستقبل',
        required=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='المستخدم المحوّل',
        default=lambda self: self.env.user
    )
    referral_date = fields.Datetime(
        string='تاريخ الإحالة',
        default=fields.Datetime.now
    )
    reason = fields.Text(
        string='سبب الإحالة',
        required=True
    )
    is_urgent = fields.Boolean(
        string='عاجل'
    )
    state = fields.Selection([
        ('pending', 'قيد الانتظار'),
        ('accepted', 'مقبول'),
        ('rejected', 'مرفوض')
    ], string='حالة الإحالة', default='pending')