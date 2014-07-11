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

class mail_group_right(osv.osv):

    _name = 'mail.group.right'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=64, required=True),
    }


class mail_group(osv.osv):

    _name = 'mail.group'
    _inherit = ['mail.group','base.recursive.model']

    _columns = {
        'type': fields.selection([('normal','Discussions'),
                                  ('circle','Circle'),
                                  ('role', 'Role')],'Type', required=True),
        'parent_id': fields.many2one('mail.group', 'Parent', select=True, ondelete='cascade'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'child_ids': fields.one2many('mail.group', 'parent_id', 'Childs'),
        'sequence': fields.integer('Sequence', select=True, help="Gives the sequence order when displaying a list of group."),
        'right_ids': fields.many2many('mail.group.right', 'mail_group_rights', 'group_id', 'right_id', 'Rights'),
        'partner_invitation_ids': fields.many2many('res.partner', 'mail_group_partner_invitations', 'group_id', 'partner_id', 'Partners invitation', readonly=True),
        'partner_group_management_ids': fields.many2many('res.partner', 'mail_group_partner_group_management', 'group_id', 'partner_id', 'Partners group management', readonly=True),
    }

    def create_partner(self, cr, uid, ids, *args):
        partner_obj = self.pool.get('res.partner')

        for group in self.browse(cr, uid, ids):
            if not group.partner_id:
                partner_id = partner_obj.create(cr, uid, {'name': group.name, 'group_id': group.id})
                self.write(cr, uid, [group.id], {'partner_id': partner_id})
        return True

    def write(self, cr, uid, ids, vals, context=None):
        partner_obj = self.pool.get('res.partner')
        old_parent_ids = []
        #_logger.info('ids %s', ids)
        if 'name' in vals:
            for group in self.browse(cr, uid, ids, context=context):
                if group.partner_id:
                    partner_obj.write(cr, uid, [group.partner_id.id], {'name':vals['name']}, context=context)
        if 'partner_id' in vals:
            for group in self.browse(cr, uid, ids, context=context):
                partner_obj.write(cr, uid, [group.partner_id.id], {'group_id': vals['partner_id'] and group.id or False}, context=context)
        if 'parent_id' in vals:
            for group in self.browse(cr, uid, ids, context=context):
                if group.parent_id:
                    old_parent_ids.append(group.parent_id.id)
        res = super(mail_group, self).write(cr, uid, ids, vals, context=context)
        if 'parent_id' in vals or 'right_ids' in vals:
            self.update_followers(cr, uid, ids, context=context)
#            _logger.info('old_parent %s', old_parent_ids)
            self.update_followers(cr, uid, old_parent_ids, context=context)
        return res



    def _check_role_no_child(self, cr, uid, ids, context=None):
        for group in self.browse(cr, uid, ids, context=context):
            if group.type == 'role' and group.child_ids:
                return False
        return True

    _constraints = [
        (_check_role_no_child, "A role can't have children", []),
    ]


    def get_right_from_children(self, cr, uid, ids, context=None):
        right_obj = self.pool.get('mail.group.right')
        right_ids = right_obj.search(cr, uid, [], context=context)
        rights = right_obj.browse(cr, uid, right_ids, context=context)

#        _logger.info('get_right_from_children ids %s', ids)
        res = {}
        for group in self.browse(cr, uid, ids, context=context):
            res[group.id] = {}
            for right in rights:
                res[group.id][right.code] = []

#            _logger.info('group %s', group)
#            _logger.info('group.child_ids %s', group.child_ids)
            for child in group.child_ids:
                child_rights = []
                for child_right in child.right_ids:
                    child_rights.append(child_right)

                for right in rights:
                    if right in child_rights:
                        res[group.id][right.code].extend([u.id for u in child.message_follower_ids])

            for right in rights:
                #deduplicate
                res[group.id][right.code] = list(set(res[group.id][right.code]))

#        _logger.info('res get_right_from_children %s', res)
        return res



    def create(self, cr, uid, vals, context=None):
        res = super(mail_group, self).create(cr, uid, vals, context=context)
        if 'parent_id' in vals and vals['parent_id']:
            self.update_followers(cr, uid, [vals['parent_id']], context=context)
        return res

    def update_followers(self, cr, uid, ids, context={}):
        fol_obj = self.pool.get('mail.followers')
        context['in_recursivity'] = True
#        _logger.info('ids %s', ids)

        rights = self.get_right_from_children(cr, uid, ids, context=context)

        parent_ids = []
        group_without_children_ids = []
        for group in self.browse(cr, uid, ids, context=context):
            vals = {}
            for right,partner_ids in rights[group.id].iteritems():
                vals['partner_' + right + '_ids'] = [(6,0, partner_ids)]
            self.write(cr, uid, [group.id], vals, context=context)
 
#            _logger.info('group %s', group)
            if group.child_ids:
                self.message_unsubscribe(cr, uid, [group.id], [p.id for p in group.message_follower_ids], context=context)
                for child in group.child_ids:
                    self.message_subscribe(cr, uid, [group.id], [p.id for p in child.message_follower_ids], context=context)
            if group.parent_id:
                parent_ids.append(group.parent_id.id)
            else:
                group_without_children_ids.append(group.id)
#        _logger.info('recursivity, parent : %s', parent_ids)
        if parent_ids:
            self.update_followers(cr, uid, parent_ids, context=context)

        if group_without_children_ids:
#            _logger.info('group_without_children_ids %s', group_without_children_ids)
            self.update_rights_descendant(cr, uid, group_without_children_ids, rights, context=context)

    def update_rights_descendant(self, cr, uid, ids, rights, context=None):

        child_ids = []
        child_rights = self.get_right_from_children(cr, uid, [c.id for group in self.browse(cr, uid, ids, context=context) for c in group.child_ids], context=context)
#        _logger.info('update_rights_descendant ids %s', ids)
#        _logger.info('rights %s', rights)
        for group in self.browse(cr, uid, ids, context=context):
#            _logger.info('name %s', group.name)

            for child in group.child_ids:
                child_ids.append(child.id)
                vals = {}
                for right,partner_from_group_ids in rights[group.id].iteritems():
                    partner_ids = child_rights[child.id][right]
#                    if child.type == 'role':
#                        partner_ids += [u.id for u in child.message_follower_ids]
                    partner_ids += partner_from_group_ids
                    child_rights[child.id][right] += partner_from_group_ids
                    partner_ids = list(set(partner_ids))
		    vals['partner_' + right + '_ids'] = [(6, 0, partner_ids)]
                self.write(cr, uid, [child.id], vals, context=context)


#        _logger.info('child_ids %s', child_ids)
        if child_ids:
            self.update_rights_descendant(cr, uid, child_ids, child_rights, context=context)
            

    def message_subscribe(self, cr, uid, ids, partner_ids, subtype_ids=None, context=None):
        res = super(mail_group, self).message_subscribe(cr, uid, ids, partner_ids, subtype_ids=subtype_ids, context=context)
        for group in self.browse(cr, uid, ids, context=context):
            if not 'in_recursivity' in context:
                self.update_followers(cr, uid, [group.id], context=context)

    def message_unsubscribe(self, cr, uid, ids, partner_ids, context=None):
        res = super(mail_group, self).message_unsubscribe(cr, uid, ids, partner_ids, context=context)
        for group in self.browse(cr, uid, ids, context=context):
            if not 'in_recursivity' in context:
                self.update_followers(cr, uid, [group.id], context=context)




class res_partner(osv.osv):

    _inherit = 'res.partner'

    _columns = {
        'group_id': fields.many2one('mail.group','Group', readonly=True)
    }
