# -*- coding: utf-8 -*-
{
    'name': "wechat_corp",
    'author': "Chanvi",
    # any module necessary for this one to work correctly
    'depends': ['auth_oauth'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/inherit_web_login.xml',
        'views/inherit_res_users.xml',
        'demo/config.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}