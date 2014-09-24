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

import openerp.addons.decimal_precision as dp

from openerp import netsvc
from openerp import pooler
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from datetime import datetime
import base64

import logging
#_logger = logging.getLogger(__name__)



class marketplace_announcement(osv.osv):

    _name = 'marketplace.announcement'
    _inherit = ['marketplace.announcement','crowdfunding.campaign']

    _columns = {
        'crowdfunding_use_funds': fields.boolean('The reserved funds will be recovered when a propasal is accepted', groups="account_wallet.group_account_wallet_moderator"),
    }

    _defaults = {
        'crowdfunding_use_funds': True,
    }
