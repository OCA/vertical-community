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

class res_partner(osv.osv):

    _inherit = 'res.partner'

    _columns = {
        'presentation': fields.text('Presentation'),
    }

class mail_group(osv.osv):

    _inherit = 'mail.group'

    _columns = {
        'manager_ids': fields.many2many('res.users', 'mail_group_res_users', 'group_id', 'user_id', 'Managers', domain=[('committee','=',True)]),
    }
