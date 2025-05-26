from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime


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

    name = fields.Char(string='Name', default=lambda self: _('Ticekts'), required=True, copy=False)
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
    subject = fields.Text(string="Subject", required=True)
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
    done_date = fields.Datetime(string="Done Date", readonly=True)
    account = fields.Many2one('res.partner', string="Account")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
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

    # def action_view_documents(self):
    #     self.ensure_one()
    #     return {
    #         'name': 'Documents',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'documents.document',
    #         'view_mode': 'kanban,tree,form',
    #         'domain': [('res_model', '=', 'ticket'), ('res_id', '=', self.id)],
    #         'context': {
    #             'default_res_model': 'ticket',
    #             'default_res_id': self.id,
    #         }
    #     }

    def _sync_documents(self):
        Document = self.env['documents.document'].sudo()
        for ticket in self:
            for attachment in ticket.attachment_ids:
                attachment.write({
                    'folder_id': ticket.documents_folder_id.id,
                    'res_model': 'ticket',
                    'res_id': ticket.id,
                })

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

    def action_open(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("يمكن فتح التذاكر في حالة مسودة فقط"))
        return self.write({'state': 'open'})

    def action_start_progress(self):
        self.ensure_one()
        if not self.assing_to_id:
            raise UserError(_("يجب تعيين التذكرة أولاً"))
        if not self.env.user.has_group('ad_smart_admin.group_ticket_technical'):
            raise UserError(_("ليس لديك صلاحية بدء المعالجة"))
        return self.write({'state': 'in_progress'})

    def action_mark_pending(self):
        return self.write({'state': 'pending'})

    def action_mark_solved(self):
        return self.write({
            'state': 'solved',
            'done_date': datetime.now()
        })

    def action_cancel(self):
        if not self.env.user.has_group('ad_smart_admin.group_ticket_manager'):
            raise UserError(_("يتطلب صلاحية مدير"))
        return self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        return self.write({'state': 'draft'})

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
        return [(record.id, f"[{record.note_number}] {record.subject}") for record in self]

    @api.model
    def create(self, vals):
        if not vals.get('note_section') or not vals.get('ticket_type'):
            raise UserError(_("القسم ونوع التذكرة مطلوبان"))

        note_section = self.env['note.section'].browse(vals['note_section'])
        ticket_type = self.env['ticket.type'].browse(vals['ticket_type'])

        if not note_section.exists() or not ticket_type.exists():
            raise UserError(_("قسم أو نوع تذكرة غير صالح"))

        # Generate sequence
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