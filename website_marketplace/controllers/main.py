# -*- coding: utf-8 -*-
import random
import simplejson
import werkzeug

from openerp import SUPERUSER_ID
from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug

class Marketplace(http.Controller):

    @http.route([
        '/marketplace/<string:type>/',
        '/marketplace/<string:type>/page/<int:page>/',
        '/marketplace/<string:type>/category/<model("marketplace.announcement.category"):category>/',
        '/marketplace/<string:type>/category/<model("marketplace.announcement.category"):category>/page/<int:page>/'
    ], type='http', auth="public", website=True, multilang=True)
    def announcements(self, type, category=None, page=0, filters='', search='', **post):
        cr, uid, context = request.cr, request.uid, request.context
        announcement_obj = request.registry.get('marketplace.announcement')
        announcement_ids = announcement_obj.search(cr, uid, [('type','=',type)], context=context)
        announcements = announcement_obj.browse(cr, uid, announcement_ids, context=context)

        values = {
            'announcements': announcements,
        }
        return request.website.render("website_marketplace.announcements", values)

    @http.route(['/marketplace/announcement/<model("marketplace.announcement"):announcement>/'], type='http', auth="public", website=True, multilang=True)
    def product(self, announcement, search='', category='', filters='', **kwargs):
        values = {
            'announcement': announcement,
        }
        return request.website.render("website_marketplace.announcement", values)
