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
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

import logging
_logger = logging.getLogger(__name__)

class mail_group(osv.osv):

    _name = 'mail.group'
    _inherit = ['mail.group','base.recursive.model']


    _columns = {
        'type': fields.selection([('normal','Discussions'),
                                  ('circle','Circle'),
                                  ('role', 'Role')],'Type', required=True),
        'parent_id': fields.many2one('mail.group', 'Parent', select=True, ondelete='cascade'),
        'child_ids': fields.one2many('mail.group', 'parent_id', 'Childs'),
        'manager_ids': fields.many2many('res.users', 'mail_group_res_users', 'group_id', 'user_id', 'Managers'),
        'sequence': fields.integer('Sequence', select=True, help="Gives the sequence order when displaying a list of group."),
        'role_ids': fields.one2many('mail.group', 'parent_id',
            domain=lambda self: [('type', '=', 'role')],
            auto_join=True,
            string='Roles'),

    }

    def _check_role_no_child(self, cr, uid, ids, context=None):
        for group in self.browse(cr, uid, ids, context=context):
            if group.type == 'role' and group.child_ids:
                return False
        return True
    _constraints = [
        (_check_role_no_child, "A role can't have children", []),
    ]



    def create(self, cr, uid, vals, context=None):
        if 'manager_ids' in vals:
            if uid not in vals['manager_ids'][0][2]:
                vals['manager_ids'] = [(6,0,[uid] + vals['manager_ids'][0][2])]
        res = super(mail_group, self).create(cr, uid, vals, context=context)
        if 'parent_id' in vals:
            self.update_followers(cr, uid, [vals['parent_id']], context=context)
        return res

    def update_followers(self, cr, uid, ids, context={}):
        fol_obj = self.pool.get('mail.followers')
        context['in_recursivity'] = True
        _logger.info('ids %s', ids)
        for group in self.browse(cr, uid, ids, context=context):
            _logger.info('group %s', group)
            if group.child_ids:
                self.message_unsubscribe(cr, uid, [group.id], [p.id for p in group.message_follower_ids], context=context)
                for child in group.child_ids:
                    self.message_subscribe(cr, uid, [group.id], [p.id for p in child.message_follower_ids], context=context)
            if group.parent_id:
                _logger.info('recursivity, parent : %s', group.parent_id)
                self.update_followers(cr, uid, [group.parent_id.id], context=context)

    def message_subscribe(self, cr, uid, ids, partner_ids, subtype_ids=None, context=None):
        res = super(mail_group, self).message_subscribe(cr, uid, ids, partner_ids, subtype_ids=subtype_ids, context=context)
        for group in self.browse(cr, uid, ids, context=context):
            if group.parent_id and not 'in_recursivity' in context:
                self.update_followers(cr, uid, [group.parent_id.id], context=context)

    def message_unsubscribe(self, cr, uid, ids, partner_ids, context=None):
        res = super(mail_group, self).message_unsubscribe(cr, uid, ids, partner_ids, context=context)
        for group in self.browse(cr, uid, ids, context=context):
            if group.parent_id and not 'in_recursivity' in context:
                self.update_followers(cr, uid, [group.parent_id.id], context=context)


    def write(self, cr, uid, ids, vals, context=None):
        old_parent_ids = []
        if 'parent_id' in vals:
            for group in self.browse(cr, uid, ids, context=context):
                if group.parent_id:
                    old_parent_ids.append(group.parent_id.id)
        res = super(mail_group, self).write(cr, uid, ids, vals, context=context)
        if 'parent_id' in vals:
            self.update_followers(cr, uid, [vals['parent_id']], context=context)
            _logger.info('old_parent %s', old_parent_ids)
            self.update_followers(cr, uid, old_parent_ids, context=context)
        return res




