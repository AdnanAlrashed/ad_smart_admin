# c:\odoo17\erpflex_odoo\addons\ad_smart_admin\models\secret_degree.py
from odoo import models, fields, _
from random import randint


CODE_SECRET_DEGREE = [
    ('top_secret', "سريه قصوى"),
    ('secret', "سريه"),
    ('low', "منخفضه"),
    ('normal', "عاديه"),
    ('other', "اخرى"),
]


class SecretDegree(models.Model):
    _name = 'secret.degree'
    _description = 'Secret Degree'

    
    name = fields.Char(string='Name', required=True)
    foreign_name = fields.Char(string='Foreign Name')
    code = fields.Selection(
        selection=CODE_SECRET_DEGREE,
        string="Code",
        copy=False, index=True,
        tracking=3,
        default='normal')
    is_default = fields.Boolean(string='Is Default')
    color = fields.Integer(string='Color')
    icon_secret = fields.Image(string='Icon')

    def name_get(self):
        return [(record.id, record.name) for record in self]
    