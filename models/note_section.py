# c:\odoo17\erpflex_odoo\addons\ad_smart_admin\models\note_section.py
from odoo import models, fields, api, _


CODE_NOTE_SECTION = [
    ('email', "Email"),
    ('sms', "SMS"),
    ('paper', "Paper"),
    ('other', "Other"),
]
class NoteSection(models.Model):
    _name = 'note.section'
    _description = 'Note Section'

    name = fields.Char(string="Name", required=True)
    foreign_name = fields.Char(string="Foreign Name")
    code = fields.Selection(
        selection=CODE_NOTE_SECTION,
        string='Code',
        required=True
    )
    connect_with = fields.Char(string="Connect With")
    connect_with_delegate = fields.Boolean(string="Connect With Delegate")
    serial_number = fields.Char(string="Serial Number", readonly=True)
    note = fields.Text(string="Note")
    sequence_id = fields.Many2one('ir.sequence', string="Sequence", readonly=True)

    def name_get(self):
        return [(record.id, record.name) for record in self]

    @api.model
    def create(self, vals):
        """إنشاء تسلسل تلقائي عند إنشاء قسم جديد"""
        note_section = super(NoteSection, self).create(vals)

        if not note_section.sequence_id:
            sequence = self.env['ir.sequence'].search([('code', '=', f"ticket.{note_section.code}")], limit=1)
            if not sequence:
                sequence = self.env['ir.sequence'].create({
                    'name': f"Sequence {note_section.name}",
                    'code': f"ticket.{note_section.code}",
                    'prefix': f"{note_section.code.upper()}/%(year)s/",
                    'padding': 4,  # 0001, 0002, 0003...
                    'company_id': False,
                })
            note_section.sequence_id = sequence.id
        
        return note_section
