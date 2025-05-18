from odoo import models, fields, api
from odoo.exceptions import UserError

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
    ]
    _order = 'date desc'
    _check_company_auto = True

    note_number = fields.Char(string="Note Number", readonly=True, copy=False)
    administration = fields.Many2one('res.users', string="Administration")
    administration_assign = fields.Many2one('res.users', string="Administration Assign")
    assing_to_id = fields.Many2one('res.users', string="Assign To")
    ticket_type = fields.Many2one('ticket.type', string="Ticket Type", default=lambda self: self._get_default_ticket_type())
    note_section = fields.Many2one('note.section', string="Note Section", required=True)
    secret_degree = fields.Many2one('secret.degree', string="Secret Degree")
    secret_degree_color = fields.Integer(related='secret_degree.color', string='Secret Degree Color', readonly=True)
    priority = fields.Many2one('priority', string="Priority")
    subject = fields.Text(string="Subject")
    topic = fields.Html(string="Topic")
    partner = fields.Many2one('res.partner', ondelete='cascade', delegate=True, required=True ,string="Partner")
    note = fields.Text(string="Note")
    date = fields.Date(string="Date")
    doc_number = fields.Integer(string="Document Number")
    balance_date = fields.Date(string="Balance Date")
    reference_number = fields.Char(string="Reference Number")
    attachment_number = fields.Integer(string="Attachment Number")
    done_date = fields.Datetime(string="Done Date")
    account = fields.Many2one('res.partner', string="Account")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    checked_archive = fields.Boolean(string="Checked Archive")

    @api.model
    def _get_default_ticket_type(self):
        """ Get the first available ticket_type """
        code = self._context.get('code')
        domain = [('code', '=', code)] if code else []  # Filter by code if available
        first_ticket_type = self.env['ticket.type'].search(domain, order='id asc', limit=1)
        return first_ticket_type.id if first_ticket_type else False
    

    def name_get(self):
        return [(record.id, record.subject) for record in self]
    
    @api.model
    def create(self, vals):
        """ توليد رقم مذكرة بناءً على القسم ونوع المذكرة """
        if vals.get('note_section') and vals.get('ticket_type'):  # تأكد من وجود note_section و ticket_type
            note_section = self.env['note.section'].browse(vals['note_section'])
            ticket_type = self.env['ticket.type'].browse(vals['ticket_type'])
            
            if note_section.exists() and ticket_type.exists():
                # إنشاء رمز التسلسل بناءً على القسم ونوع المذكرة
                sequence_code = f"memo.{note_section.code.lower()}.{ticket_type.code.lower()}"
                
                # البحث عن التسلسل الموجود أو إنشائه إذا لم يكن موجودًا
                sequence = self.env['ir.sequence'].search([('code', '=', sequence_code)], limit=1)
                if not sequence:
                    sequence = self.env['ir.sequence'].create({
                        'name': f"Memo Sequence for {note_section.name} - {ticket_type.name}",
                        'code': sequence_code,
                        'prefix': f"{note_section.code}/{ticket_type.code}/",  # مثال: SEC/TYP/00001
                        'padding': 5,  # عدد الأرقام في التسلسل (مثال: 00001)
                        'number_increment': 1,  # زيادة التسلسل بمقدار 1
                    })
                
                # توليد رقم المذكرة
                vals['note_number'] = sequence.next_by_id() or 'NEW'
            else:
                raise ValueError("Invalid note_section or ticket_type provided.")
        else:
            raise ValueError("note_section and ticket_type are required.")
        return super(Ticket, self).create(vals)
    
    