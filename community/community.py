# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Buron
#    Copyright 2013 Yannick Buron
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

import logging
#_logger = logging.getLogger(__name__)

class community_init(osv.osv):
    _name = "community.init"

    def _community_init(self, cr, uid):
        icp = self.pool.get('ir.config_parameter')
        icp.set_param(cr, uid, 'auth_signup.allow_uninvited', True)
        icp.set_param(cr, uid, 'auth_signup.reset_password', True)


class groups_view(osv.osv):
    _inherit = 'res.groups'


    def get_simplified_groups_by_application(self, cr, uid, context=None):
        """ return all groups classified by application (module category), as a list of pairs:
                [(app, kind, [group, ...]), ...],
            where app and group are browse records, and kind is either 'boolean' or 'selection'.
            Applications are given in sequence order.  If kind is 'selection', the groups are
            given in reverse implication order.
        """
        model  = self.pool.get('ir.model.data')

        res = super(groups_view, self).get_simplified_groups_by_application(cr, uid, context=context)

        #_logger.info('In community get_simplified')

        #We need to catch the exception for the community module installation, the records are not created at this point
        try:
            category = model.get_object(cr, uid, 'community', 'module_category_community')
            group_community_user = model.get_object(cr, uid, 'community', 'group_community_user')
            group_community_administrator = model.get_object(cr, uid, 'community', 'group_community_administrator')
            res.append((category, 'selection', [group_community_user,group_community_administrator]))

            category = model.get_object(cr, uid, 'base', 'module_category_website')
            group_website_publisher = model.get_object(cr, uid, 'base', 'group_website_publisher')
            group_website_designer = model.get_object(cr, uid, 'base', 'group_website_designer')
            res.append((category, 'selection', [group_website_publisher,group_website_designer]))

            category = model.get_object(cr, uid, 'base', 'module_category_knowledge_management')
            group_document_user = model.get_object(cr, uid, 'base', 'group_document_user')
            res.append((category, 'selection', [group_document_user]))

            category = model.get_object(cr, uid, 'gamification', 'module_goal_category')
            group_goal_manager = model.get_object(cr, uid, 'gamification', 'group_goal_manager')
            res.append((category, 'selection', [group_goal_manager]))

            category = model.get_object(cr, uid, 'community', 'module_category_community')
            group_membership_moderator = model.get_object(cr, uid, 'membership_users', 'group_membership_moderator')
            res.append((category, 'boolean', [group_membership_moderator]))

        except ValueError:
            pass

        return res


