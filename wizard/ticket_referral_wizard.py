from odoo import models, fields, api

class TicketReferralWizard(models.TransientModel):
    _name = 'ticket.referral.wizard'
    _description = 'معالج إحالة التذكرة'

    # التعديل على ديفولت ديناميكي
    @api.model
    def default_get(self, fields):
        res = super(TicketReferralWizard, self).default_get(fields)
        ticket_id = self.env.context.get('default_ticket_id')
        if ticket_id:
            ticket = self.env['ticket'].browse(ticket_id)
            res.update({
                'from_department_id': ticket.current_department_id.id,
                'to_department_id': False  # تأكيد مسح أي قيمة افتراضية
            })
        return res
    
    # تحديث الدومين ديناميكياً
    @api.onchange('from_department_id')
    def _onchange_from_department(self):
        domain = {}
        if self.from_department_id:
            domain = {'to_department_id': [('id', '!=', self.from_department_id.id)]}
        return {'domain': domain}
    
    ticket_id = fields.Many2one(
        'ticket',
        string='التذكرة',
        required=True
    )
    # الحقول المعدلة
    from_department_id = fields.Many2one(
        'hr.department',
        string='القسم المرسل',
        readonly=True
    )
    to_department_id = fields.Many2one(
        'hr.department',
        string='القسم المستقبل',
        required=True,
        domain="[('id', '!=', from_department_id)]"  # منع اختيار نفس القسم
    )
    reason = fields.Text(
        string='سبب الإحالة',
        required=True
    )
    is_urgent = fields.Boolean(
        string='عاجل'
    )
    
    def action_confirm_referral(self):
        self.ensure_one()
        # إنشاء سجل الإحالة
        referral = self.env['ticket.referral'].create({
            'ticket_id': self.ticket_id.id,
            'from_department_id': self.from_department_id.id,
            'to_department_id': self.to_department_id.id,
            'reason': self.reason,
            'is_urgent': self.is_urgent,
            'user_id': self.env.user.id
        })
        
        # تحديث التذكرة
        self.ticket_id.write({
            'current_department_id': self.to_department_id.id,
            'state': 'referred'
        })
        
        # إرسال إشعار بشكل صحيح
        partner_ids = []
        
        # 1. إضافة مدير القسم المستقبل
        if self.to_department_id.manager_id.user_id.partner_id:
            partner_ids.append(self.to_department_id.manager_id.user_id.partner_id.id)
        
        # 2. إضافة أعضاء الفريق (إذا كان هناك مجموعة مستخدمين للقسم)
        team_users = self.env['res.users'].search([
            ('department_id', '=', self.to_department_id.id)
        ])
        partner_ids += team_users.mapped('partner_id').ids
        
        # 3. إزالة التكرارات
        partner_ids = list(set(partner_ids))
        
        # 4. إرسال الإشعار
        self.ticket_id.sudo().message_post(
            body=f"""
            <p>تم إحالة التذكرة <strong>{self.ticket_id.name}</strong></p>
            <p>من قسم: {self.from_department_id.name}</p>
            <p>إلى قسم: {self.to_department_id.name}</p>
            <p>السبب: {self.reason}</p>
            <p>الحالة: {'عاجل' if self.is_urgent else 'عادي'}</p>
            """,
            subject=f"إحالة تذكرة جديدة: {self.ticket_id.name}",
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
            partner_ids=partner_ids,
            email_layout_xmlid='mail.mail_notification_light'
        )
        
        # إغلاق النموذج
        return {
            'type': 'ir.actions.act_window_close'
        }
# This code defines a wizard for referring tickets in an administrative system.
# It allows users to select a ticket, specify the sending and receiving departments,
# provide a reason for the referral, and mark it as urgent if needed.
# The wizard ensures that the receiving department is different from the sending department