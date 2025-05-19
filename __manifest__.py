{
    'name': "Smart_Admin",
    'summary': "Administrative communications system",
    'description': """
            This system provides all administrative communications services for all institutions.
    """,
    'author': "Adnan_Alrashed",
    'website': "http://yourwebsite.com",
    'category': 'Tools',
    'version': '17.0.1.0.0',
    'depends': ['base','web','mail', 'hr', 'rating', 'utm','portal'],
    'data': [
        # 'views/assets.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',  # صلاحيات الوصول
        'security/record_rules.xml',  # صلاحيات الوصول
        'views/sa_ticket_type_view.xml',          # واجهات انواع المذكرات
        'views/menu.xml',                # القوائم الجانبية
        'views/sa_ticket_view.xml',                #  واجهة المذكرات الصادر والوارد
        'views/sa_note_section_view.xml',                #  واجهة اقسام المذكره
        'views/sa_secret_degree_view.xml',                #  واجهة درجة السريه
        'views/sa_priority_view.xml',                #  واجهة الاولويات
    ],
#     'assets': {
#     'web.assets_backend': [
#         '/ad_smart_admin/static/src/js/script.js',
#         'your_module/static/src/xml/template.xml',
#     ],
# },

    
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

