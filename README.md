## 简述
Odoo 企业微信应用对接模块，实现Oauth2网页授权登录，自定义odoo业务消息推送。
for odoo10, odoo11

## 特性
1. oauth登录与odoo用户登陆互不影响。
2. 无需安装额外python模块依赖，开箱即用。
3. 一键同步企业微信用户并关联。
4. 使用标签管理企业微信用户组更灵活，可随意删除标签名。

## 使用
1. 把模块wechat_corp克隆到addons目录或自定义addons目录下。
2. 更新应用列表并安装模块，安装成功后会出现“企业微信”顶级菜单。
3. 配置企业微信
4. 同步用户
5. 自定义消息发送：
```
    self.env['wxcorp.messages'].send(touser='admin', content='你有条新消息')
```
6. 详细参考：[详细说明.docx](https://github.com/chanvi/odoo_wechat_corp/raw/master/%E8%AF%A6%E7%BB%86%E8%AF%B4%E6%98%8E.docx)
