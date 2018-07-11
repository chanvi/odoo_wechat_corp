# -*- coding: utf-8 -*-
{
    'name': "wechat_corp",
    'author': "Chanvi",
    'website': 'https://github.com/chanvi',
    'summary': "Odoo 企业微信应用对接模块，实现Oauth2网页授权登录，自定义odoo业务消息推送。",
    'depends': ['auth_oauth'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
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