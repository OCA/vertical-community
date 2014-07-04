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
_logger = logging.getLogger(__name__)



class marketplace_announcement(osv.osv):

    _inherit = 'marketplace.announcement'

    def _prepare_task_values(self, cr, uid, vals, context=None):
        res = super(marketplace_announcement, self)._prepare_task_values(cr, uid, vals, context=context)

        sender = partner_obj.browse(cr, uid, vals['sender_id'], context=context)
        if sender.group_id:
            res['role_id'] = sender.group_id
        return res

class marketplace_proposition(osv.osv):

    _inherit = 'marketplace.proposition'

    def _prepare_task_values(self, cr, uid, proposition, context=None):
        res = super(marketplace_proposition, self)._prepare_task_values(cr, uid, proposition, context=context)

        if proposition.sender_id.group_id:
            res['role_id'] = proposition.sender_id.group_id
        return res

class project_task(osv.osv):

    _inherit = 'project.task'

    _columns = {
        'marketplace_announcer': fields.selection([('user','The user of the task'),
                                              ('role','The role assigned to the task'),
                                              ('circle','The circle of the role, you must have the wallet right for this')], 'Who will create the announce?', required=True)
    }

    _defaults = {
        'marketplace_announcer': 'user'
    }


    def _prepare_announcement_values(self, cr, uid, task, context=None):
        res = super(project_task, self)._prepare_announcement_values(cr, uid, task, context=context)
        user_partner_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).partner_id.id
        if task.marketplace_announcer in ['role','circle']:
            if not task.role_id:
                raise osv.except_osv(_('Access error!'),_("No role assigned to this task!"))
            if task.marketplace_announcer == 'circle':
                if task.role_id == 'role' and task.role_id.parent_id:
                    if user_partner_id in task.role_id.parent_id.partner_wallet_ids:
                        res['partner_id'] = task.role_id.parent_id.partner_id.id
                    else:
                        raise osv.except_osv(_('Access error!'),_("You must have the wallet right in the circle!"))
                else:
                    res['partner_id'] = task.role_id.partner_id.id
        return res

    def _update_assigned_user(self, cr, uid, ids, vals, context=None):
        res = super(project_task, self)._update_assigned_user(cr, uid, ids, vals, context=context)
        if 'stage_id' in vals:
            for task in self.browse(cr, uid, ids, context=context):
                for config in task.assigned_user_config_result_ids:
                    if config.stage_id.id == vals['stage_id'] and task.parent_ids and task.proposition_id and config.marketplace_assignment:
                        if config.marketplace_assignment == 'sender' and task.proposition_id.type == 'want' or config.marketplace_assignment == 'invoicer' and task.proposition_id.type == 'offer':
                            self.write(cr, uid, [task.id], {'role_id': task.parent_ids[0].role_id.id}, context=context)
                        if config.marketplace_assignment == 'sender' and task.proposition_id.type == 'offer' or config.marketplace_assignment == 'invoicer' and task.proposition_id.type == 'want' and task.proposition_id.partner_id.group_id:
                            self.write(cr, uid, [task.id], {'role_id': task.proposition_id.partner_id.group_id.id}, context=context)

        return res

