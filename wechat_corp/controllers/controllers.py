# -*- coding: utf-8 -*-
# @Author Chanvi
# @Version 1.0
# github: https://github.com/chanvi/odoo_wechat_corp

from odoo import http, api, SUPERUSER_ID

from odoo.http import request
import werkzeug.utils

from CorpApi import *
from odoo import registry as registry_get
import logging
_logger = logging.getLogger(__name__)


class Wechat(http.Controller):
    @http.route('/wechat/open/', auth='public')
    def open(self):
        '''企业微信oauth_url'''
        dbname = request.session.db
        registry = registry_get(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, {})
                config = env['wechat.corp.config'].sudo().search([('id', '=', 1)])[0]
                if  config:
                    corp_id = config.corp_id
                    host = request.httprequest.environ.get('HTTP_HOST', '')
                    url = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=%s&redirect_uri=http://%s/wechat/wechat&response_type=code&scope=SCOPE&connect_redirect=1#wechat_redirect'%(corp_id,host)
            except Exception as e:
                _logger.exception("open: %s" % str(e))
                url = "/web/login?oauth_error=2"

        return self.set_cookie_and_redirect(url)

    @http.route('/wechat/wechat/', auth='public')
    def oauth(self, **kw):
        '''企业微信oauth验证'''
        code = request.params.get('code')

        dbname = request.session.db
        registry = registry_get(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, {})
                config = env['wechat.corp.config'].sudo().search([('id', '=', 1)])[0]
                if config:
                    corp_id = config.corp_id
                    corp_agent_secret = config.corp_agent_secret
            except Exception as e:
                _logger.exception("oauth: %s" % str(e))

        # 调用企业微信api
        if code and corp_id and corp_agent_secret:
            wxapi = CorpApi(corp_id, corp_agent_secret)
            try:
                accesstoken = wxapi.getAccessToken()
                response = wxapi.httpCall(
                    CORP_API_TYPE['GET_USER_INFO_BY_CODE'],
                    {
                        "code":code
                    }
                )
                _logger.info(u'UserId:%s'%response['UserId'])
                if response['UserId']:
                    with registry.cursor() as cr:
                        try:
                            env = api.Environment(cr, SUPERUSER_ID, {})
                            wechat_corp_users_id = env['wechat.corp.users'].sudo().search([('userid', '=', response['UserId'])])[0]
                            res_users_id = env['res.users'].sudo().search([('wxcorp_users_id', '=', wechat_corp_users_id.id)])[0]
                            login = res_users_id.login
                            if login:
                                # 更新访问令牌
                                res_users_id.write({"oauth_access_token": accesstoken})
                                cr.commit()
                                # 验证核心函数authenticate：数据库名，登录名，密码或访问令牌
                                request.session.authenticate(dbname, login, accesstoken)
                                url = '/web'
                            else:
                                url = '/web/login?oauth_error=2'
                        except Exception as e:
                            _logger.exception("oauth_res_users: %s" % str(e))
                            url = '/web/login?oauth_error=2'
            except ApiException as e:
                # print e.errCode, e.errMsg
                _logger.info(u'errMsg:%s' % e.errMsg)
                url = '/web/login?oauth_error=2'
        else:
            url = '/web/login?oauth_error=2'
        return self.set_cookie_and_redirect(url)

    def set_cookie_and_redirect(self, redirect_url):
        '''跳转处理'''
        redirect = werkzeug.utils.redirect(redirect_url, 303)
        redirect.autocorrect_location_header = False
        return redirect