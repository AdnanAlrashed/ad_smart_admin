from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class Ticket(models.Model):
    _name = 'ticket'
    _description = 'Ticket'
    _inherit = [
        'portal.mixin',
        'mail.thread.cc',
        'utm.mixin',
        'rating.mixin',
        'mail.activity.mixin',
        'mail.tracking.duration.mixin',
        'ir.attachment',
    ]
    _order = 'date desc'
    _check_company_auto = True
    # أضف هذه الدالة في بداية النموذج
    @api.model
    def _get_current_user_department(self):
        """Get the current user's department"""
        user = self.env.user
        if user.employee_ids:
            return user.employee_ids[0].department_id.id
        return False

    # قم بتعديل الحقول الموجودة لتكون كالتالي:
    company_id = fields.Many2one(
        'res.company', 
        string="Company", 
        default=lambda self: self.env.company,
        readonly=True
    )

    current_department_id = fields.Many2one(
        'hr.department',
        string='القسم الحالي',
        tracking=True,
        default=lambda self: self._get_current_user_department(),
        readonly=True
    )
    # name = fields.Char(string='Name', default=lambda self: _('Ticekts'), required=True, copy=False)
    name = fields.Char(string='Subject', required=True, index=True, tracking=True)
    note_number = fields.Char(string="Note Number", default=lambda self: _('New'), required=True, copy=False)
    administration = fields.Many2one('res.users', string="Administration")
    administration_assign = fields.Many2one('res.users', string="Administration Assign")
    assing_to_id = fields.Many2one('res.users', string="Assign To")
    ticket_type = fields.Many2one('ticket.type', string="Ticket Type", 
                                default=lambda self: self._get_default_ticket_type())
    note_section = fields.Many2one('note.section', string="Note Section", required=True)
    secret_degree = fields.Many2one('secret.degree', string="Secret Degree")
    secret_degree_color = fields.Integer(related='secret_degree.color', string='Secret Degree Color', readonly=True)
    priority = fields.Many2one('priority', string="Priority")
    # subject = fields.Text(string="Subject", required=True)
    topic = fields.Html(string="Topic")
    from_partner = fields.Many2one('res.partner', deleget=True, ondelete='restrict', string="From Partner")
    to_partner = fields.Many2one(
        'res.partner',
        deleget=True,
        string='الى الجهة',
        ondelete='restrict',
        domain="[('is_company', '=', True)]",
        help="الجهة التي سيتم توجيه التذكرة إليها"
    )
    note = fields.Text(string="Note")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    doc_number = fields.Integer(string="Document Number")
    balance_date = fields.Date(string="Balance Date")
    reference_number = fields.Char(string="Reference Number")
    attachment_number = fields.Integer(string="Attachment Number", compute='_compute_attachments')
    # done_date = fields.Datetime(string="Done Date")
    account = fields.Many2one('res.partner', string="Account")
    # company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    checked_archive = fields.Boolean(string="Checked Archive")

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='المرفقات',
        relation='ticket_attachment_rel',
        column1='ticket_id',
        column2='attachment_id',
        help='الملفات المرفقة مع التذكرة'
    )

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('open', 'مفتوحة'),
        ('referred', 'محولة'),  # الحالة الجديدة
        ('in_progress', 'قيد المعالجة'),
        ('pending', 'معلقة'),
        ('solved', 'تم الحل'),
        ('cancelled', 'ملغاة')
    ], string='حالة التذكرة', default='draft', tracking=True, group_expand='_expand_states')

    documents_folder_id = fields.Many2one(
        'documents.folder',
        string='مجلد المستندات',
        store=True,
        readonly=False,
        help='المجلد المخصص لحفظ مرفقات هذه التذكرة'
    )

    document_count = fields.Integer(
    string='عدد المستندات',
    compute='_compute_document_count',
    store=False
)

    duration = fields.Float(
    string="مدة المعالجة (ساعات)",
    compute='_compute_duration',
    store=True,
    help="المدة من بدء المعالجة حتى الحل"
)

    @api.depends('create_date', 'done_date')
    def _compute_duration(self):
        for ticket in self:
            if ticket.create_date and ticket.done_date:
                delta = ticket.done_date - ticket.create_date
                ticket.duration = delta.total_seconds() / 3600  # التحويل إلى ساعات
            else:
                ticket.duration = 0.0

    # --------------------------SLA Start----------
    
    resolution_time_hours = fields.Float(compute='_compute_resolution_time')  # الوقت الفعلي
    sla_deadline = fields.Datetime(string="موعد SLA النهائي", tracking=True)
    sla_state = fields.Selection([
        ('on_time', 'ضمن الوقت المحدد'),
        ('warning', 'تحذير'),
        ('breached', 'تم تجاوز الموعد')
    ], string="حالة SLA", compute='_compute_sla_state', store=True)
    sla_response_time = fields.Integer(string="وقت الاستجابة المستهدف (ساعات)", default=24)
    sla_resolution_time = fields.Integer(string="وقت الحل المستهدف (ساعات)", default=72) # الوقت المستهدف
    
    # الحقول الجديدة
    draft_date = fields.Datetime(string="تاريخ المسودة", readonly=True, copy=False)
    open_date = fields.Datetime(string="تاريخ الفتح", readonly=True, copy=False)
    in_progress_date = fields.Datetime(string="تاريخ بدء المعالجة", readonly=True, copy=False)
    pending_date = fields.Datetime(string="تاريخ التعليق", readonly=True, copy=False)
    solved_date = fields.Datetime(string="تاريخ الحل", readonly=True, copy=False)
    cancelled_date = fields.Datetime(string="تاريخ الإلغاء", readonly=True, copy=False)
    
    # تحديث حقل done_date ليكون تلقائياً عند الحل
    done_date = fields.Datetime(string="تاريخ الإنجاز", readonly=True, copy=False)

     # إضافة الحقول الجديدة الخاصة بالإحالات
    referral_ids = fields.One2many(
        'ticket.referral', 
        'ticket_id', 
        string='سجل الإحالات'
    )
    # current_department_id = fields.Many2one(
    #     'hr.department',
    #     string='القسم الحالي',
    #     tracking=True
    # )
    referral_count = fields.Integer(
        compute='_compute_referral_count',
        string='عدد الإحالات'
    )
    
    def _compute_referral_count(self):
        for ticket in self:
            ticket.referral_count = len(ticket.referral_ids)
    
    def action_open_referral_wizard(self):
        # تأكيد وجود القسم الحالي
        if not self.current_department_id:
            raise UserError("يجب تعيين قسم حالي للتذكرة قبل الإحالة")
        return {
            'type': 'ir.actions.act_window',
            'name': 'إحالة التذكرة',
            'res_model': 'ticket.referral.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
                'default_from_department_id': self.current_department_id.id,
                'default_is_urgent': False
            }
        }

    def _track_state_changes(self, new_state):
        """تسجيل تواريخ تغيير الحالة تلقائياً"""
        now = fields.Datetime.now()
        state_date_field = f"{new_state}_date"
        
        if state_date_field in self._fields and not self[state_date_field]:
            self.write({state_date_field: now})
            
        # إذا كانت الحالة solved، نحدّث done_date تلقائياً
        if new_state == 'solved' and not self.done_date:
            self.write({'done_date': now})

    @api.depends('sla_deadline', 'state')
    def _compute_sla_state(self):
        now = fields.Datetime.now()
        for ticket in self:
            if not ticket.sla_deadline or ticket.state in ['solved', 'cancelled']:
                ticket.sla_state = False
            elif ticket.sla_deadline < now:
                ticket.sla_state = 'breached'
            elif (ticket.sla_deadline - timedelta(hours=2)) < now:
                ticket.sla_state = 'warning'
            else:
                ticket.sla_state = 'on_time'
    
    # @api.model
    # def create(self, vals):
    #     ticket = super(Ticket, self).create(vals)
    #     if ticket.state == 'open':
    #         ticket._update_sla_deadline()
    #     return ticket
    
    def write(self, vals):
        res = super(Ticket, self).write(vals)
        if 'state' in vals or 'sla_response_time' in vals or 'sla_resolution_time' in vals:
            self._update_sla_deadline()
        return res
    
    def _update_sla_deadline(self):
        for ticket in self:
            if ticket.state == 'open':
                ticket.sla_deadline = fields.Datetime.now() + timedelta(hours=ticket.sla_response_time)
            elif ticket.state == 'in_progress':
                ticket.sla_deadline = fields.Datetime.now() + timedelta(hours=ticket.sla_resolution_time)
    # --------------------------SLA End----------
    @api.depends('open_date', 'in_progress_date', 'solved_date', 'pending_date')
    def _compute_resolution_time(self):
        for ticket in self:
            if not ticket.open_date or not ticket.solved_date:
                ticket.resolution_time_hours = 0.0
                continue
                
            total_time = (ticket.solved_date - ticket.open_date).total_seconds() / 3600
            
            # خصم وقت التعليق من الحساب
            if ticket.pending_date and ticket.in_progress_date:
                if ticket.pending_date > ticket.in_progress_date:  # تم التعليق بعد البدء
                    pending_duration = min(ticket.solved_date or datetime.max, 
                                    ticket.in_progress_date or datetime.max) - ticket.pending_date
                    total_time -= pending_duration.total_seconds() / 3600
            
            ticket.resolution_time_hours = max(0, total_time)  # تجنب القيم السالبة
    # --------------------------الوقت المتبقي--------------------------
    sla_remaining_text = fields.Char(
    string="الوقت المتبقي",
    compute='_compute_sla_remaining',
    store=False
)

    def _compute_sla_remaining(self):
        now = fields.Datetime.now()
        for ticket in self:
            if not ticket.sla_deadline:
                ticket.sla_remaining_text = False
            else:
                delta = ticket.sla_deadline - now
                ticket.sla_remaining_text = f"متبقي: {delta.days} أيام, {delta.seconds//3600} ساعات"
    # --------------------------الوقت المتبقي--------------------------

    def _send_sla_notifications(self):
        now = fields.Datetime.now()
        for ticket in self:
            if not ticket.sla_deadline or ticket.state in ['solved', 'cancelled']:
                continue
                
            time_remaining = (ticket.sla_deadline - now).total_seconds() / 3600
            
            if time_remaining <= 0:
                ticket._send_notification(
                    'انتهاء وقت SLA',
                    f'تم تجاوز الموعد النهائي لتذكرة {ticket.note_number}'
                )
            elif time_remaining <= 2:  # تحذير قبل ساعتين
                ticket._send_notification(
                    'اقتراب موعد SLA',
                    f'تبقى {round(time_remaining, 1)} ساعات لإنهاء تذكرة {ticket.note_number}'
                )

# نستدعي هذه الدالة من cron job أو عند تغيير الحالة

    def _check_sla_deadlines(self):
        tickets = self.search([
            ('sla_state', 'in', ['warning', 'breached']),
            ('state', 'not in', ['solved', 'cancelled'])
        ])
        
        for ticket in tickets:
            if ticket.sla_state == 'breached':
                ticket._send_notification(
                    'SLA Breached!',
                    f'تم تجاوز الموعد النهائي لتذكرة {ticket.note_number}'
                )
            elif ticket.sla_state == 'warning':
                ticket._send_notification(
                    'SLA Warning',
                    f'تبقى ساعتان فقط على موعد SLA لتذكرة {ticket.note_number}'
                )

    def _send_notification(self, subject, body):
        self.ensure_one()
        self.message_post(
            subject=subject,
            body=body,
            partner_ids=[(6, 0, [self.assing_to_id.partner_id.id])],
            message_type='notification'
        )

    sla_performance = fields.Float(
    string="أداء SLA (%)",
    compute='_compute_sla_performance',
    store=True,  # اختياري - يخزن القيمة في DB
    digits=(3, 2),  # دقة رقمية (3 أرقام قبل العلامة، رقمين بعدها)
    help="نسبة تحقيق أهداف SLA بناءً على وقت الحل الفعلي vs المستهدف"
)

    @api.depends('resolution_time_hours', 'sla_resolution_time', 'state')
    def _compute_sla_performance(self):
        for ticket in self:
            if ticket.state != 'solved':
                ticket.sla_performance = 0.0
                continue
                
            if not ticket.sla_resolution_time or ticket.resolution_time_hours <= 0:
                ticket.sla_performance = 0.0
            else:
                # معادلة الأداء (يمكن تعديلها حسب احتياجاتك)
                performance = (ticket.sla_resolution_time / ticket.resolution_time_hours) * 100
                ticket.sla_performance = min(120.0, max(0.0, performance))  # حد أدنى 0% وأقصى 120%

    def _compute_document_count(self):
        Document = self.env['documents.document'].sudo()
        for record in self:
            record.document_count = Document.search_count([
                ('res_model', '=', 'ticket'),
                ('res_id', '=', record.id)
            ])


    def _compute_attachments(self):
        for ticket in self:
            ticket.attachment_number = len(ticket.attachment_ids)

    def open_attachments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'مرفقات التذكرة',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'domain': [('res_id', '=', self.id), ('res_model', '=', 'ticket')],
            'context': {
                'default_res_model': 'ticket',
                'default_res_id': self.id,
            }
        }


    def _sync_documents(self):
        Document = self.env['documents.document'].sudo()
        existing_docs = Document.search_read([
            ('res_model', '=', 'ticket'),
            ('res_id', 'in', self.ids)
        ], fields=['attachment_id', 'res_id'])

        existing_map = {
            (doc['attachment_id'], doc['res_id']) for doc in existing_docs
        }

        for ticket in self:
            for attachment in ticket.attachment_ids:
                key = (attachment.id, ticket.id)
                if key not in existing_map:
                    Document.create({
                        'name': attachment.name,
                        'attachment_id': attachment.id,
                        'folder_id': ticket.documents_folder_id.id,
                        'owner_id': ticket.assing_to_id.id or self.env.user.id,
                        'res_model': 'ticket',
                        'res_id': ticket.id,
                    })

    def action_open(self):
        for ticket in self:
            if ticket.state != 'draft':
                raise UserError(_("يمكن فتح التذاكر في حالة مسودة فقط"))
            ticket.write({'state': 'open'})
            ticket._track_state_changes('open')

    def action_start_progress(self):
        for ticket in self:
            if not ticket.assing_to_id:
                raise UserError(_("يجب تعيين التذكرة أولاً"))
            if not self.env.user.has_group('ad_smart_admin.group_ticket_technical'):
                raise UserError(_("ليس لديك صلاحية بدء المعالجة"))
            ticket.write({'state': 'in_progress'})
            ticket._track_state_changes('in_progress')

    def action_mark_pending(self):
        for ticket in self:
            if not ticket.assing_to_id:
                raise UserError(_("يجب تعيين التذكرة أولاً"))
            if not self.env.user.has_group('ad_smart_admin.group_ticket_technical'):
                raise UserError(_("ليس لديك صلاحية بدء المعالجة"))
            ticket.write({'state': 'pending'})
            ticket._track_state_changes('pending')

    def action_mark_solved(self):
        for ticket in self:
            if not ticket.assing_to_id:
                raise UserError(_("يجب تعيين التذكرة أولاً"))
            if not self.env.user.has_group('ad_smart_admin.group_ticket_technical'):
                raise UserError(_("ليس لديك صلاحية بدء المعالجة"))
            ticket.write({'state': 'solved'})
            ticket._track_state_changes('solved')
    def action_cancel(self):
        for ticket in self:
            if not ticket.assing_to_id:
                raise UserError(_("يجب تعيين التذكرة أولاً"))
            if not self.env.user.has_group('ad_smart_admin.group_ticket_technical'):
                raise UserError(_("ليس لديك صلاحية بدء المعالجة"))
            ticket.write({'state': 'cancelled'})
            ticket._track_state_changes('cancelled')
    def action_reset_to_draft(self):
        for ticket in self:
            if not ticket.assing_to_id:
                raise UserError(_("يجب تعيين التذكرة أولاً"))
            if not self.env.user.has_group('ad_smart_admin.group_ticket_technical'):
                raise UserError(_("ليس لديك صلاحية بدء المعالجة"))
            ticket.write({'state': 'draft'})
            ticket._track_state_changes('draft')

    # --------------------------
    # Helper Methods
    # --------------------------
    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    @api.model
    def _get_default_ticket_type(self):
        """Get the first available ticket_type with context support"""
        code = self._context.get('code')
        domain = [('code', '=', code)] if code else []
        ticket_type = self.env['ticket.type'].search(domain, order='id asc', limit=1)
        return ticket_type.id if ticket_type else False

    # --------------------------
    # Overridden Methods
    # --------------------------
    def name_get(self):
        return [(record.id, f"[{record.note_number}] {record.name}") for record in self]

    # @api.model
    # def create(self, vals):
    #     if not vals.get('note_section') or not vals.get('ticket_type'):
    #         raise UserError(_("القسم ونوع التذكرة مطلوبان"))

    #     note_section = self.env['note.section'].browse(vals['note_section'])
    #     ticket_type = self.env['ticket.type'].browse(vals['ticket_type'])

    #     if not note_section.exists() or not ticket_type.exists():
    #         raise UserError(_("قسم أو نوع تذكرة غير صالح"))

    #     # Generate sequence
    #     sequence_code = f"memo.{note_section.code.lower()}.{ticket_type.code.lower()}"
    #     sequence = self.env['ir.sequence'].sudo().search([('code', '=', sequence_code)], limit=1)

    #     if not sequence:
    #         sequence = self.env['ir.sequence'].sudo().create({
    #             'name': f"تسلسل {note_section.name} - {ticket_type.name}",
    #             'code': sequence_code,
    #             'prefix': f"{note_section.code}/{ticket_type.code}/",
    #             'padding': 5,
    #             'number_increment': 1,
    #         })

    #     vals['note_number'] = sequence.next_by_id() or 'NEW'

    #     if not vals.get('documents_folder_id'):
    #         parent_folder = self.env['documents.folder'].sudo().search([('name', '=', 'Tickets')], limit=1)
    #         if not parent_folder:
    #             parent_folder = self.env['documents.folder'].sudo().create({'name': 'Tickets'})
    #         folder = self.env['documents.folder'].sudo().create({
    #             'name': f"مرفقات التذكرة {vals.get('note_number', 'جديد')}",
    #             'company_id': vals.get('company_id') or self.env.company.id,
    #             'parent_folder_id': parent_folder.id,
    #         })
    #         vals['documents_folder_id'] = folder.id

    #     ticket = super(Ticket, self).create(vals)
    #     ticket._sync_documents()
    #     return ticket

    @api.model
    def create(self, vals):
        if not vals.get('note_section') or not vals.get('ticket_type'):
            raise UserError(_("القسم ونوع التذكرة مطلوبان"))

        note_section = self.env['note.section'].browse(vals['note_section'])
        ticket_type = self.env['ticket.type'].browse(vals['ticket_type'])

        if not note_section.exists() or not ticket_type.exists():
            raise UserError(_("قسم أو نوع تذكرة غير صالح"))

        sequence_code = f"memo.{note_section.code.lower()}.{ticket_type.code.lower()}"
        sequence = self.env['ir.sequence'].sudo().search([('code', '=', sequence_code)], limit=1)

        if not sequence:
            sequence = self.env['ir.sequence'].sudo().create({
                'name': f"تسلسل {note_section.name} - {ticket_type.name}",
                'code': sequence_code,
                'prefix': f"{note_section.code}/{ticket_type.code}/",
                'padding': 5,
                'number_increment': 1,
            })

        vals['note_number'] = sequence.next_by_id() or 'NEW'

        if not vals.get('documents_folder_id'):
            parent_folder = self.env['documents.folder'].sudo().search([('name', '=', 'Tickets')], limit=1)
            if not parent_folder:
                parent_folder = self.env['documents.folder'].sudo().create({'name': 'Tickets'})
            folder = self.env['documents.folder'].sudo().create({
                'name': f"مرفقات التذكرة {vals.get('note_number', 'جديد')}",
                'company_id': vals.get('company_id') or self.env.company.id,
                'parent_folder_id': parent_folder.id,
            })
            vals['documents_folder_id'] = folder.id

        ticket = super(Ticket, self).create(vals)

        if ticket.state == 'open':
            ticket._update_sla_deadline()

        ticket._sync_documents()
        return ticket


    def write(self, vals):
        result = super(Ticket, self).write(vals)
        for ticket in self:
            if not ticket.documents_folder_id:
                parent_folder = self.env['documents.folder'].sudo().search([('name', '=', 'Tickets')], limit=1)
                if not parent_folder:
                    parent_folder = self.env['documents.folder'].sudo().create({'name': 'Tickets'})
                folder = self.env['documents.folder'].sudo().create({
                    'name': f"مرفقات التذكرة {ticket.note_number or 'جديد'}",
                    'company_id': ticket.company_id.id,
                    'parent_folder_id': parent_folder.id,
                })
                ticket.documents_folder_id = folder
        self._sync_documents()
        return result

    def action_force_sync_documents(self):
        Document = self.env['documents.document'].sudo()
        Attachment = self.env['ir.attachment'].sudo()

        for ticket in self:
            # تأكد من وجود المجلد
            if not ticket.documents_folder_id:
                parent_folder = self.env['documents.folder'].sudo().search([('name', '=', 'Tickets')], limit=1)
                if not parent_folder:
                    parent_folder = self.env['documents.folder'].sudo().create({'name': 'Tickets'})
                folder = self.env['documents.folder'].sudo().create({
                    'name': f"مرفقات التذكرة {ticket.note_number or 'جديد'}",
                    'company_id': ticket.company_id.id,
                    'parent_folder_id': parent_folder.id,
                })
                ticket.documents_folder_id = folder

            # ابحث عن كل المرفقات المرتبطة بالتذكرة مباشرة
            attachments = Attachment.search([
                ('res_model', '=', 'ticket'),
                ('res_id', '=', ticket.id)
            ])

            for attachment in attachments:
                # تحقق هل لها مستند موجود مسبقًا
                existing_doc = Document.search([
                    ('attachment_id', '=', attachment.id),
                    ('res_model', '=', 'ticket'),
                    ('res_id', '=', ticket.id)
                ], limit=1)

                if not existing_doc:
                    Document.create({
                        'name': attachment.name,
                        'attachment_id': attachment.id,
                        'folder_id': ticket.documents_folder_id.id,
                        'owner_id': ticket.assing_to_id.id or self.env.user.id,
                        'res_model': 'ticket',
                        'res_id': ticket.id,
                    })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents Synced',
            'res_model': 'documents.document',
            'view_mode': 'kanban,tree,form',
            'domain': [('res_model', '=', 'ticket'), ('res_id', '=', self.ids)],
            'context': {
                'default_res_model': 'ticket',
                'default_res_id': self.ids,
            }
        }
