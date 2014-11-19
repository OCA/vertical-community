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

from openerp.osv import fields, osv

_logger = logging.getLogger(__name__)


class MarketplaceAnnouncement(osv.osv):

    """
    Make sure the users who has wallet right on the group has
    the corresponding rights on the announcement.
    Also, announcement can now be made in the context of a group.
    """

    _inherit = 'marketplace.announcement'

    def _get_user_role(self, cr, uid, ids, prop, unknow_none, context=None):
        res = super(MarketplaceAnnouncement, self)._get_user_role(
            cr, uid, ids, prop, unknow_none, context=context
        )
        partner_id = self.pool.get('res.users').browse(
            cr, uid, uid, context=context
        ).partner_id.id
        for announcement in self.browse(cr, uid, ids, context=context):
            if announcement.partner_id.group_id and partner_id in \
                [p.id for p in
                 announcement.partner_id.group_id.partner_wallet_ids]:
                res[announcement.id]['is_user'] = True
        return res

    _columns = {
        'context_group_ids': fields.many2many(
            'mail.group', 'marketplace_announcement_group_rel',
            'announcement_id', 'group_id', 'Groups'
        ),
        'is_user': fields.function(
            _get_user_role, type="boolean", string="Is user?", multi='role'
        ),
    }
