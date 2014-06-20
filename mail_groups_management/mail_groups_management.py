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

class mail_group(osv.osv):

    _inherit = 'mail.group'

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if not context:
            context = {}
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)


    _columns = {
        'type': fields.selection([('normal','Discussions'),
                                  ('circle','Circle'),
                                  ('role', 'Role')],'Type', required=True),
        'manager_ids': fields.many2many('res.users', 'mail_group_res_users', 'group_id', 'user_id', 'Managers'),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Name'),
        'parent_id': fields.many2one('mail.group','Parent Group', select=True),
        'child_id': fields.one2many('mail.group', 'parent_id', string='Child Groups'),
        'sequence': fields.integer('Sequence', select=True, help="Gives the sequence order when displaying a list of group."),
        'parent_left': fields.integer('Left Parent', select=1),
        'parent_right': fields.integer('Right Parent', select=1),
        'role_ids': fields.one2many('mail.group', 'parent_id',
            domain=lambda self: [('type', '=', 'role')],
            auto_join=True,
            string='Roles'),

    }

    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'sequence, name'
    _order = 'parent_left'

    def _check_role_no_child(self, cr, uid, ids, context=None):
        for group in self.browse(cr, uid, ids, context=context):
            if group.type == 'role' and group.child_id:
                return False
        return True
    _constraints = [
        (osv.osv._check_recursion, 'Error ! You cannot create recursive categories.', ['parent_id']),
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
        for group in self.browse(cr, uid, ids, context=context):
            if group.child_id:
                self.message_unsubscribe(cr, uid, [group.id], [p.id for p in group.message_follower_ids], context=context)
                for child in group.child_id:
                    self.message_subscribe(cr, uid, [group.id], [p.id for p in child.message_follower_ids], context=context)
            if group.parent_id:
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
                old_parent_ids.append(group.parent_id.id)
        res = super(mail_group, self).write(cr, uid, ids, vals, context=context)
        if 'parent_id' in vals:
            self.update_followers(cr, uid, [vals['parent_id']], context=context)
            self.update_followers(cr, uid, old_parent_ids, context=context)
        return res




