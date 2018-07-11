# -*- coding: utf-8 -*-
# @Author Chanvi
# @Version 1.0
# github: https://github.com/chanvi/odoo_wechat_corp

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from CorpApi import *
import logging
import odoo.osv.osv

_logger = logging.getLogger(__name__)

class wechat_corp_config(models.Model):
    _name = 'wechat.corp.config'
    _rec_name = 'corp_agent'
    _description = u'企业微信配置'

    corp_id = fields.Char('企业 CorpID')
    corp_agent = fields.Char('应用 AgentId', default='0')
    corp_agent_secret = fields.Char('应用 Secret')
    corp_secret = fields.Char('通讯录 Secret')
    first = fields.Boolean(u'占位字段')

    @api.onchange('corp_id', 'corp_agent', 'corp_agent_secret', 'corp_secret')
    def _onchange_filter_spaces(self):
        """过滤首尾空格"""
        self.corp_id = self.corp_id.strip() if self.corp_id else ''
        self.corp_agent = self.corp_agent.strip() if self.corp_agent else ''
        self.corp_agent_secret = self.corp_agent_secret.strip() if self.corp_agent_secret else ''
        self.corp_secret = self.corp_secret.strip() if self.corp_secret else ''

class wechat_corp_users(models.Model):
    _name = 'wechat.corp.users'
    _description = u'企业微信用户'

    name =  fields.Char('姓名', required = True)
    userid = fields.Char('账号', required = True)
    gender = fields.Selection([(1, '男'), (2, '女')], string='性别')
    mobile = fields.Char('手机号' )
    email = fields.Char('邮箱' )
    position = fields.Char('职位')
    status = fields.Selection([(1, '已关注'), (2, '已禁用'), (4, '未关注')], string='状态', default=4)
    avatar = fields.Char('头像')
    department = fields.Integer('部门')

    _sql_constraints = [
        ('userid_key', 'UNIQUE (userid)',  '账号已存在 !'),
        ('mobile_key', 'UNIQUE (mobile)', '手机号已存在 !'),
        ('email_key', 'UNIQUE (email)',  '邮箱已存在 !'),
    ]

    @api.model
    def create(self, values, only_create=0):
        """创建时同步到企业微信"""
        if not (values.get('mobile') or values.get('email') ):
            raise ValidationError(u'手机和邮箱不能同时为空')

        # 添加用户到企业微信(only_create=1时则不新增成员到企业微信)
        if not only_create:
            config = self.env['wechat.corp.config'].browse(1)
            if not (config.corp_id and config.corp_secret):
                raise odoo.osv.osv.except_osv(u'未配置', u'请先配置企业微信！')
            try:
                wxapi = CorpApi(config.corp_id, config.corp_secret)
                values['department'] = 1
                response = wxapi.httpCall(CORP_API_TYPE['USER_CREATE'],values)
                _logger.info('wechat_corp_users create: %s' % str(response))
            except ApiException as e:
                raise ValidationError(u'请求企业微信服务器异常: %s 异常信息: %s' % (e.errCode, e.errMsg))
        # 执行原create逻辑
        return super(wechat_corp_users, self).create(values)

    @api.multi
    def unlink(self):
        """删除用户同步到企业微信"""
        config = self.env['wechat.corp.config'].browse(1)
        for rec in self:
            try:
                wxapi = CorpApi(config.corp_id, config.corp_secret)
                response = wxapi.httpCall(CORP_API_TYPE['USER_DELETE'], {'userid' : rec.userid})
                _logger.info('wechat_corp_users unlink: %s' % str(response))
            except ApiException as e:
                raise ValidationError(u'请求企业微信服务器异常: %s 异常信息: %s' % (e.errCode, e.errMsg))
        # 执行原unlink逻辑
        return super(wechat_corp_users, self).unlink()

    @api.multi
    def write(self, values):
        """编辑用户同步到企业微信"""
        res = super(wechat_corp_users, self).write(values)
        if not (self.mobile or self.email):
            raise ValidationError('手机和邮箱不能同时为空')
        values['userid'] = self.userid  #只读字段并不传值，但更新企业微信用户必须要有userid
        config = self.env['wechat.corp.config'].browse(1)
        try:
            wxapi = CorpApi(config.corp_id, config.corp_secret)
            response = wxapi.httpCall(CORP_API_TYPE['USER_UPDATE'], values)
            _logger.info('wechat_corp_users write: %s' % str(response))
        except ApiException as e:
            raise ValidationError(u'请求企业微信服务器异常: %s 异常信息: %s' % (e.errCode, e.errMsg))
        return res

    @api.model
    def sync_users(self):
        """一键同步：先从企业微信上把用户同步下来，再从系统用户以增量方式同步到企业微信"""
        # 从企业微信同步用户
        config = self.env['wechat.corp.config'].browse(1)
        if not (config.corp_id and config.corp_secret):
            raise odoo.osv.osv.except_osv(u'未配置', u'请先配置企业微信！')
        try:
            wxapi = CorpApi(config.corp_id, config.corp_secret)
            response = wxapi.httpCall(
                CORP_API_TYPE['USER_LIST'],
                {
                    'department_id': '1',
                    'fetch_child': '1'
                }
            )
            # print(response)
            for userlist in response.get('userlist'):
                # 如果手机号已经存在，则不同步
                if userlist.get('mobile'):
                    res = self.search([('mobile', '=', userlist.get('mobile'))]).exists()
                    if res: continue

                # 如果email已经存在，则不同步
                if userlist.get('email'):
                    res = self.search([('email', '=', userlist.get('email'))]).exists()
                    if res: continue

                try:
                    self.create({
                        'name': userlist['name'] if userlist['name']!='' else None,
                        'userid': userlist['userid'] if userlist['userid']!='' else None,
                        'email': userlist['email'] if userlist['email']!='' else None,
                        'mobile': userlist['mobile'] if userlist['mobile']!='' else None,
                    },only_create=1)
                except Exception as e:
                    raise ValidationError(u'从企业微信同步异常，异常信息: %s' %e)

        except ApiException as e:
            raise ValidationError(u'请求企业微信服务器异常: %s 异常信息: %s' % (e.errCode, e.errMsg))

        # 从系统用户同步
        res_users = self.env['res.users'].search([('wxcorp_mobile','!=','')])
        for rec in res_users:
            # 如果手机号已经存在，则不同步
            if rec.wxcorp_mobile:
                res = self.search([('mobile', '=', rec.wxcorp_mobile)]).exists()
                if res:
                    # 如果手机号存在又没关联的用户，则关联
                    if not rec.wxcorp_users_id:rec.write({'wxcorp_users_id': res.id})
                    continue

            # 判断用户login是否以email的形式存在
            import re
            is_email = re.match('\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*', str(rec.login))
            # 如果email已经存在，则不同步
            if is_email:
                res = self.search([('email', '=', rec.login)]).exists()
                if res: continue

            res_users_email = rec.login if is_email else ''
            try:
                ret = self.create({
                    'name': rec.name,
                    'userid': rec.login,
                    'email': res_users_email,
                    'mobile': rec.wxcorp_mobile,
                })
                rec.write({'wxcorp_users_id': ret.id})

            except Exception as e:
                raise ValidationError(u'同步异常，异常信息: %s' %e)
        self.env.cr.commit()
        raise odoo.osv.osv.except_osv(u'一键同步',u'同步完毕！')

class wxcorp_messages(models.Model):
    _name = 'wxcorp.messages'
    _description = u'企业微信应用消息'

    touser = fields.Char('成员ID列表')
    # toparty = fields.Char('部门ID列表')
    totag = fields.Char('标签ID列表')
    content = fields.Text('消息内容')

    @api.model
    def send(self, touser='', totag='', content=''):
        content = content.replace('"',"'")
        config = self.env['wechat.corp.config'].browse(1)
        if not (config.corp_id and config.corp_agent_secret and config.corp_agent):
            raise odoo.osv.osv.except_osv(u'发送消息失败', u'请先配置好企业微信！')

        wxapi = CorpApi(config.corp_id, config.corp_agent_secret)
        try:
            response = wxapi.httpCall(
                CORP_API_TYPE['MESSAGE_SEND'],
                {
                    "touser": touser,
                    "totag": totag,
                    "msgtype": "text",
                    "agentid": config.corp_agent,
                    "text": {
                        "content": content
                    },
                    "safe": 0
                }
            )
            # print response['errmsg']
            if response['errmsg']=='ok':
                self.create({
                    'touser': touser,
                    'totag': totag,
                    'content': content,
                })
                self.env.cr.commit()
        except ApiException as e:
            raise odoo.osv.osv.except_osv(u'消息发送', u'消息发送失败：%s,%s'%(e.errCode, e.errMsg))

class wechat_corp_totag(models.Model):
    _name = 'wechat.corp.totag'
    _description = u'标签'
    _rec_name = 'tagname'

    tagname = fields.Char(u'标签名称', required = True)
    tagid = fields.Char(u'标签ID')
    userlist_ids = fields.Many2many('wechat.corp.users', string="用户列表")

    _sql_constraints = [
        ('tagname_key', 'UNIQUE (tagname)',  '标签名已存在 !')
    ]

    @api.model
    def create(self, values):
        """创建标签时同步到企业微信"""
        # 添加标签到企业微信
        config = self.env['wechat.corp.config'].browse(1)
        if not (config.corp_id and config.corp_secret):
            raise odoo.osv.osv.except_osv(u'未配置', u'请先配置企业微信！')
        try:
            wxapi = CorpApi(config.corp_id, config.corp_secret)
            response = wxapi.httpCall(CORP_API_TYPE['TAG_CREATE'],values)
            values['tagid'] = response['tagid']
        except ApiException as e:
            raise ValidationError(u'请求企业微信服务器异常: %s 异常信息: %s' % (e.errCode, e.errMsg))
        # 执行原create逻辑
        return super(wechat_corp_totag, self).create(values)

    @api.multi
    def unlink(self):
        '''删除标签同步到企业微信'''
        config = self.env['wechat.corp.config'].browse(1)
        for rec in self:
            try:
                wxapi = CorpApi(config.corp_id, config.corp_secret)
                wxapi.httpCall(CORP_API_TYPE['TAG_DELETE'], {'tagid' : rec.tagid})
            except ApiException as e:
                raise ValidationError(u'请求企业微信服务器异常: %s 异常信息: %s' % (e.errCode, e.errMsg))
        # 执行原unlink逻辑
        return super(wechat_corp_totag, self).unlink()

    @api.multi
    def write(self, values):
        '''
        编辑标签同步到企业微信
        添加标签所属用户
        '''
        # res = super(wechat_corp_totag, self).write(values)

        config = self.env['wechat.corp.config'].browse(1)
        wxapi = CorpApi(config.corp_id, config.corp_secret)
        values['tagid'] = self.tagid    # 隐藏的字段并不会传值
        # 修改标签名
        if values.get('tagname') and values.get('tagid'):
            try:
                response = wxapi.httpCall(CORP_API_TYPE['TAG_UPDATE'], values)
            except ApiException as e:
                raise ValidationError(u'请求企业微信服务器异常: %s 异常信息: %s' % (e.errCode, e.errMsg))

        # 编辑用户列表
        # 先清除标签已有的用户成员
        if self.userlist_ids:
            userlist = []
            for rec in self.userlist_ids:
                userlist.append(rec.userid)
            values['userlist'] = userlist

            try:
                response = wxapi.httpCall(CORP_API_TYPE['TAG_DELETE_USER'], values)
            except ApiException as e:
                raise ValidationError(u'请求企业微信服务器异常: %s 异常信息: %s' % (e.errCode, e.errMsg))

        # 添加用户到标签
        if values.get('userlist_ids'):
            user_id_list = values.get('userlist_ids')[0][2]

            if user_id_list:
                wechat_corp_users = self.env['wechat.corp.users'].search([('id', 'in', user_id_list)])
                userlist = []
                for rec in wechat_corp_users:
                    userlist.append(rec.userid)
                values['userlist'] = userlist
                try:
                    wxapi.httpCall(CORP_API_TYPE['TAG_ADD_USER'], values)
                except ApiException as e:
                    raise ValidationError(u'请求企业微信服务器异常: %s 异常信息: %s' % (e.errCode, e.errMsg))

        return super(wechat_corp_totag, self).write(values)