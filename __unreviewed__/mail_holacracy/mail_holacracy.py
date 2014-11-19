# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Buron. Copyright Yannick Buron
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging

from openerp.osv import fields, osv, orm
from openerp import SUPERUSER_ID
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class MailGroupRight(osv.osv):

    """
    Define rights which can be assigned to children groups of a circle.
    Theses rights shall be created by depending modules.
    """

    _name = 'mail.group.right'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=64, required=True),
    }


class MailGroup(osv.osv):

    """
    Improve mail.group to make it recursive and manage holacracy concepts
    """

    _name = 'mail.group'
    _inherit = ['mail.group', 'base.recursive.model']

    _columns = {
        'type': fields.selection([
            ('normal', 'Discussions'),
            ('circle', 'Circle'),
            ('role', 'Role')
        ], 'Type', required=True),
        'parent_id': fields.many2one(
            'mail.group', 'Parent', select=True, ondelete='cascade'
        ),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'child_ids': fields.one2many('mail.group', 'parent_id', 'Childs'),
        'sequence': fields.integer(
            'Sequence', select=True,
            help="Sets the displaying sequence order for a group list."
        ),
        'right_ids': fields.many2many(
            'mail.group.right', 'mail_group_rights',
            'group_id', 'right_id', 'Rights'
        ),
        'partner_invitation_ids': fields.many2many(
            'res.partner', 'mail_group_partner_invitations',
            'group_id', 'partner_id', 'Partners invitation', readonly=True
        ),
        'partner_group_management_ids': fields.many2many(
            'res.partner', 'mail_group_partner_group_management',
            'group_id', 'partner_id', 'Partners group management',
            readonly=True
        ),
    }

    _defaults = {
        'type': 'normal'
    }

    def _check_role_no_child(self, cr, uid, ids, context=None):
        # Check if the group is role and have children
        for group in self.browse(cr, uid, ids, context=context):
            if group.type == 'role' and group.child_ids:
                return False
        return True

    _constraints = [
        (_check_role_no_child, "A role can't have children", []),
    ]

    def create_partner(self, cr, uid, ids, *args):
        # Function called by button to create a partner linked to the group
        partner_obj = self.pool.get('res.partner')
        for group in self.browse(cr, uid, ids):
            if not group.partner_id:
                partner_id = partner_obj.create(
                    cr, uid, {'name': group.name, 'group_id': group.id}
                )
                self.write(cr, uid, [group.id], {'partner_id': partner_id})
        return True

    def create(self, cr, uid, vals, context=None):
        # Refresh followers list and partner linked when creating the group
        partner_obj = self.pool.get('res.partner')
        res = super(MailGroup, self).create(cr, uid, vals, context=context)
        if 'parent_id' in vals and vals['parent_id']:
            self.update_followers(
                cr, uid, [vals['parent_id']], context=context
            )
        if 'partner_id' in vals:
            partner_obj.write(
                cr, uid, [vals['partner_id']], {'group_id': False},
                context=context
            )
        return res

    def write(self, cr, uid, ids, vals, context=None):
        # Refresh followers list and partner linked
        # when partner_id or parent_id change
        partner_obj = self.pool.get('res.partner')
        old_parent_ids = []

        old_partner_ids = []
        if 'partner_id' in vals:
            for group in self.browse(cr, uid, ids, context=context):
                if group.partner_id:
                    old_partner_ids.append(group.partner_id.id)
        if 'parent_id' in vals:
            for group in self.browse(cr, uid, ids, context=context):
                if group.parent_id:
                    old_parent_ids.append(group.parent_id.id)
        res = super(MailGroup, self).write(cr, uid, ids, vals, context=context)
        if 'parent_id' in vals or 'right_ids' in vals:
            self.update_followers(cr, uid, ids, context=context)
            self.update_followers(cr, uid, old_parent_ids, context=context)

        if 'partner_id' in vals:
            if vals['partner_id']:
                partner_obj.write(
                    cr, uid, [vals['partner_id']],
                    {'group_id': False}, context=context
                )
            if old_partner_ids:
                partner_obj.write(
                    cr, uid, old_partner_ids,
                    {'group_id': False}, context=context
                )

        if 'name' in vals:
            for group in self.browse(cr, uid, ids, context=context):
                if group.partner_id:
                    partner_obj.write(
                        cr, uid, [group.partner_id.id],
                        {'name': vals['name']}, context=context
                    )
        return res

    def get_right_from_children(self, cr, uid, ids, context=None):
        # Return for each group the list of users for each rights
        right_obj = self.pool.get('mail.group.right')
        right_ids = right_obj.search(cr, uid, [], context=context)
        rights = right_obj.browse(cr, uid, right_ids, context=context)

        res = {}
        for group in self.browse(cr, uid, ids, context=context):
            res[group.id] = {}
            for right in rights:
                res[group.id][right.code] = []

            for child in group.child_ids:
                child_rights = []
                for child_right in child.right_ids:
                    child_rights.append(child_right)

                for right in rights:
                    if right in child_rights:
                        res[group.id][right.code].extend(
                            [u.id for u in child.message_follower_ids]
                        )

            for right in rights:
                #deduplicate
                res[group.id][right.code] = list(
                    set(res[group.id][right.code])
                )

        return res

    def update_followers(self, cr, uid, ids, context={}):
        # Update the followers for specified groups but also his children
        # and his parents. This function is recursive on the up side and
        #  then update rights on children if the group has no parents
        context['in_recursivity'] = True

        rights = self.get_right_from_children(cr, uid, ids, context=context)

        parent_ids = []
        group_without_parent_ids = []
        for group in self.browse(cr, uid, ids, context=context):
            vals = {}
            for right, partner_ids in rights[group.id].iteritems():
                vals['partner_' + right + '_ids'] = [(6, 0, partner_ids)]
            self.write(cr, uid, [group.id], vals, context=context)

            if group.child_ids:
                self.message_unsubscribe(
                    cr, uid, [group.id],
                    [p.id for p in group.message_follower_ids], context=context
                )
                for child in group.child_ids:
                    self.message_subscribe(
                        cr, uid, [group.id],
                        [p.id for p in child.message_follower_ids],
                        context=context
                    )
            if group.parent_id:
                parent_ids.append(group.parent_id.id)
            else:
                group_without_parent_ids.append(group.id)

        if parent_ids:
            self.update_followers(cr, uid, parent_ids, context=context)

        if group_without_parent_ids:
            self.update_rights_descendant(
                cr, uid, group_without_parent_ids, rights, context=context
            )

    def update_rights_descendant(self, cr, uid, ids, rights, context=None):
        # Called by groups without parent to update rights of
        # all children groups. Recursive function

        child_ids = []
        child_rights = self.get_right_from_children(
            cr, uid,
            [c.id for group in self.browse(cr, uid, ids, context=context)
             for c in group.child_ids], context=context
        )
        for group in self.browse(cr, uid, ids, context=context):

            for child in group.child_ids:
                child_ids.append(child.id)
                vals = {}
                for right, partner_from_group_ids \
                        in rights[group.id].iteritems():
                    partner_ids = child_rights[child.id][right]
                    partner_ids += partner_from_group_ids
                    child_rights[child.id][right] += partner_from_group_ids
                    partner_ids = list(set(partner_ids))
                    vals['partner_' + right + '_ids'] = [(6, 0, partner_ids)]
                self.write(cr, uid, [child.id], vals, context=context)

        if child_ids:
            self.update_rights_descendant(
                cr, uid, child_ids, child_rights, context=context
            )

    def message_subscribe(
            self, cr, uid, ids, partner_ids, subtype_ids=None, context={}
    ):
        # Override message_subscribe to recompute followers on parents
        # when someone subscribe to a group
        res = super(MailGroup, self).message_subscribe(
            cr, uid, ids, partner_ids,
            subtype_ids=subtype_ids, context=context
        )
        for group in self.browse(cr, uid, ids, context=context):
            if not 'in_recursivity' in context or 'in_recursivity' \
                    in context and not context['in_recursivity']:
                self.update_followers(
                    cr, SUPERUSER_ID, [group.id], context=context
                )

    def message_unsubscribe(self, cr, uid, ids, partner_ids, context={}):
        # Override message_subscribe to recompute followers on parents
        # when someone unsubscribe from a group
        res = super(MailGroup, self).message_unsubscribe(
            cr, uid, ids, partner_ids, context=context
        )
        for group in self.browse(
                cr, uid, ids, context=context
        ):
            if not 'in_recursivity' in context \
                    or 'in_recursivity' in context \
                    and not context['in_recursivity']:
                self.update_followers(
                    cr, SUPERUSER_ID, [group.id], context=context
                )


class ResPartner(osv.osv):

    """
    Add link to mail.group in res.partner
    """

    _inherit = 'res.partner'

    def _get_group(self, cr, uid, ids, prop, unknow_none, context=None):
        # Get the group linked to the partner.
        # We use a function field on the partner side to simulate a one2one
        group_obj = self.pool.get('mail.group')

        res = {}
        for partner in self.browse(cr, uid, ids, context=context):
            res[partner.id] = False

            group_ids = group_obj.search(
                cr, uid, [('partner_id', '=', partner.id)], context=context
            )
            if group_ids:
                res[partner.id] = group_ids[0]

        return res


    _columns = {
        'group_id': fields.function(
            _get_group, type="many2one",
            relation="mail.group", string="Group", readonly=True, store=True
        ),
    }