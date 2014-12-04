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

from openerp.osv import orm

_logger = logging.getLogger(__name__)


class GroupsView(orm.Model):

    """
    Add group in user simplified form
    """
    _inherit = 'res.groups'

    def get_simplified_groups_by_application(self, cr, uid, context=None):
        """ return all groups classified by application (module category),
        as a list of pairs: [(app, kind, [group, ...]), ...],
        where app and group are browse records, and kind is either 'boolean'
        or 'selection'. Applications are given in sequence order. If kind is
        'selection', the groups are given in reverse implication order.
        """
        model = self.pool.get('ir.model.data')

        res = super(GroupsView, self).get_simplified_groups_by_application(
            cr, uid, context=context
        )

        # We need to catch the exception for the community module installation,
        # the records are not created at this point
        try:
            category = model.get_object(
                cr, uid, 'base', 'module_category_sales_management'
            )
            group_sale_salesman = model.get_object(
                cr, uid, 'base', 'group_sale_salesman'
            )
            group_sale_salesman_all_leads = model.get_object(
                cr, uid, 'base', 'group_sale_salesman_all_leads'
            )
            group_sale_manager = model.get_object(
                cr, uid, 'base', 'group_sale_manager'
            )
            res.append((
                category, 'selection',
                [group_sale_salesman, group_sale_salesman_all_leads,
                 group_sale_manager]
            ))

        except ValueError:
            pass

        return res
