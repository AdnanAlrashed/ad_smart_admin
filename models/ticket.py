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

    # --------------------------
    # Existing Fields
    # --------------------------
    note_number = fields.Char(string="Note Number", readonly=True, copy=False)
    administration = fields.Many2one('res.users', string="Administration")
    administration_assign = fields.Many2one('res.users', string="Administration Assign")
    assing_to_id = fields.Many2one('res.users', string="Assign To")
    ticket_type = fields.Many2one('ticket.type', string="Ticket Type", 
                                default=lambda self: self._get_default_ticket_type())
    note_section = fields.Many2one('note.section', string="Note Section", required=True)
    secret_degree = fields.Many2one('secret.degree', string="Secret Degree")
    secret_degree_color = fields.Integer(related='secret_degree.color', 
                                      string='Secret Degree Color', readonly=True)
    priority = fields.Many2one('priority', string="Priority")
    subject = fields.Text(string="Subject", required=True)
    topic = fields.Html(string="Topic")
    partner = fields.Many2one('res.partner', ondelete='cascade', 
                            delegate=True, required=True, string="Partner")
    note = fields.Text(string="Note")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    doc_number = fields.Integer(string="Document Number")
    balance_date = fields.Date(string="Balance Date")
    reference_number = fields.Char(string="Reference Number")
    attachment_number = fields.Integer(string="Attachment Number", compute='_compute_attachments')
    done_date = fields.Datetime(string="Done Date", readonly=True)
    account = fields.Many2one('res.partner', string="Account")
    company_id = fields.Many2one('res.company', string="Company", 
                               default=lambda self: self.env.company)
    checked_archive = fields.Boolean(string="Checked Archive")
    message_main_attachment_id = fields.Many2one(
        'ir.attachment',
        string="المرفق الرئيسي",
        index=True
    )
    
    # --------------------------
    # Enhanced Workflow Fields
    # --------------------------
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('open', 'مفتوحة'),
        ('in_progress', 'قيد المعالجة'),
        ('pending', 'معلقة'),
        ('solved', 'تم الحل'),
        ('cancelled', 'ملغاة')
    ], string='حالة التذكرة', default='draft', tracking=True, group_expand='_expand_states')
    
    # --------------------------
    # Computed Fields
    # --------------------------
    def _compute_attachments(self):
        for ticket in self:
            ticket.attachment_number = self.env['ir.attachment'].search_count([
                ('res_model', '=', 'ticket'),
                ('res_id', '=', ticket.id)
            ])

    # --------------------------
    # Workflow Methods
    # --------------------------

    

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
        return super(Ticket, self).create(vals)