# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Inherit_res_users(models.Model):
    _inherit = 'res.users'

    wxcorp_users_id = fields.Many2one('wechat.corp.users', string=u'关联企业微信用户')
    wxcorp_mobile = fields.Char(string=u'手机号')

    _sql_constraints = [
        ('wxcorp_mobile_key', 'UNIQUE (wxcorp_mobile)', '手机号已存在 !')
    ]