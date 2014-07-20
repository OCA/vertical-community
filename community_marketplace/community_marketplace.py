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

        #We need to catch the exception for the community module installation, the records are not created at this point
        try:
            category = model.get_object(cr, uid, 'account_centralbank', 'module_centralbank_category')
            group_account_centralbank_user = model.get_object(cr, uid, 'account_centralbank', 'group_account_centralbank_user')
            group_account_centralbank_moderator = model.get_object(cr, uid, 'account_centralbank', 'group_account_centralbank_moderator')
            res.append((category, 'selection', [group_account_centralbank_user,group_account_centralbank_moderator]))

        except ValueError:
            pass

        return res


