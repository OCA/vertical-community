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
_logger = logging.getLogger(__name__)

class community_init(osv.osv):
    _name = "community.init"

    def _community_init(self, cr, uid):
        icp = self.pool.get('ir.config_parameter')
        icp.set_param(cr, uid, 'auth_signup.allow_uninvited', True)
        icp.set_param(cr, uid, 'auth_signup.reset_password', True)


class res_users(osv.osv):

    _inherit = 'res.users'

    _columns = {
        'committee': fields.boolean('Committee?'),
        'moderator': fields.boolean('Moderator?'),
    }

    def create(self, cr, uid, values, context=None):
        res = super(res_users, self).create(cr, uid, values, context=context)
        self.update_community_rights(cr, uid, [res], values, context=context)
        return res

    def write(self, cr, uid, ids, values, context=None):

        res = super(res_users, self).write(cr, uid, ids, values, context=context)
        self.update_community_rights(cr, uid, ids, values, context=context)
        return res

    def update_community_rights(self, cr, uid, ids, values, context=None):
        model  = self.pool.get('ir.model.data')
        group_obj = self.pool.get('res.groups')


        _logger.info('values %s', values)

        if 'moderator' in values:
            if values['moderator']:
                values['committee'] = True

        if 'committee' in values:
            if values['committee']:
                moderator_group_id = model.get_object(cr, uid, 'community', 'group_community_committee').id
                for id in ids:
                    group_obj.write(cr, uid, [moderator_group_id], {'users': [(4, id)]}, context=context)
            else:
                group_ids = group_obj.search(cr, uid, [('name', 'not in',['Portal','Anonymous'])], context=context)
                base_group_id = model.get_object(cr, uid, 'community', 'group_community_user').id
                for id in ids:
                    group_obj.write(cr, uid, group_ids, {'users': [(3, id)]}, context=context)
                    group_obj.write(cr, uid, [base_group_id], {'users': [(4, id)]}, context=context)
        if 'moderator' in values:
            if values['moderator']:
                moderator_group_id = model.get_object(cr, uid, 'community', 'group_community_moderator').id
                for id in ids:
                    group_obj.write(cr, uid, [moderator_group_id], {'users': [(4, id)]}, context=context)
            else:
                group_ids = group_obj.search(cr, uid, [('name', 'not in',['Portal','Anonymous'])], context=context)
                base_group_id = model.get_object(cr, uid, 'community', 'group_community_user').id
                for user in self.browse(cr, uid, ids, context=context):
                    if user.committee and not 'committee' in values or 'committee' in values and values['committee']:
                        base_group_id = model.get_object(cr, uid, 'community', 'group_community_committee').id
                    group_obj.write(cr, uid, group_ids, {'users': [(3, user.id)]}, context=context)
                    group_obj.write(cr, uid, [base_group_id], {'users': [(4, user.id)]}, context=context)


