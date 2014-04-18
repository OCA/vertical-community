# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
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
import openerp.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class vote_type(osv.osv):
    _name = 'vote.type'

    _columns = {
        'name': fields.char('Name', size=128, required=True),
    }
vote_type()


class vote_config_settings(osv.osv):
    _name = 'vote.config.settings'
    _description = 'Vote configuration'

    _columns = {
        'line_ids': fields.one2many('vote.config.line', 'res_id',
            domain=lambda self: [('model', '=', self._name)],
            auto_join=True,
            string='Lines'),
    }

vote_config_settings()

class vote_config_line(osv.osv):
    _name = 'vote.config.line'

    _columns = {
        'model': fields.char('Related Document Model', size=128, select=1),
        'res_id': fields.integer('Related Document ID', select=1),
        'target_model': fields.many2one('ir.model', 'Target model', ondelete='cascade'),
        'name': fields.many2one('vote.type', 'Name', required=True),
        'action': fields.selection([('add','Add'),('remove','Remove')], 'Action'),
        'sequence': fields.integer('Sequence'),
    }

    _order = 'target_model, sequence'
vote_config_line()

class vote_config_line_stored(osv.osv):
    _name = 'vote.config.line.stored'

    _columns = {
        'model': fields.char('Related Document Model', size=128, select=1),
        'res_id': fields.integer('Related Document ID', select=1),
        'name': fields.many2one('vote.type', 'Name', required=True),
        'sequence': fields.integer('Sequence'),
    }

    _order = 'sequence'
vote_config_line_stored()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
