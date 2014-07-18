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



class project_task(osv.osv):

    _inherit = 'project.task'

    def _get_marketplace(self, cr, uid, ids, prop, unknow_none, context=None):
        announcement_obj = self.pool.get('marketplace.announcement')
        proposition_obj = self.pool.get('marketplace.proposition')

        res = {}
        for task in self.browse(cr, uid, ids, context=context):
            res[task.id] = {}
            res[task.id]['announcement_id'] = False
            res[task.id]['proposition_id'] = False

            announcement_ids = announcement_obj.search(cr, uid, [('task_id','=',task.id)], context=context)
            if announcement_ids:
                res[task.id]['announcement_id'] = announcement_ids[0]

            proposition_ids = proposition_obj.search(cr, uid, [('task_id','=',task.id)], context=context)
            if proposition_ids:
                res[task.id]['proposition_id'] = proposition_ids[0]

        return res


    _columns = {
        #Tried to make a store with a function but it doesn't work because when we change the value we have in the function only the announcement id of the new task, we can't update the old one.
        'announcement_id': fields.function(_get_marketplace, type="many2one", relation="marketplace.announcement", string="Announcement", readonly=True, multi="marketplace", store=True),
        'proposition_id': fields.function(_get_marketplace, type="many2one", relation="marketplace.proposition", string="Proposition", readonly=True, multi="marketplace", store=True),
    }

    def _prepare_announcement_values(self, cr, uid, task, context=None):
        announcement_vals = {
            'name': task.name,
            'description':task.description,
            'task_id': task.id,
            'partner_id': task.user_id.partner_id.id
        }
        return announcement_vals


    def create_announcement(self, cr, uid, ids, *args):

        announcement_obj = self.pool.get('marketplace.announcement')

        for task in self.browse(cr, uid, ids):
            if not task.announcement_id:
                announcement_vals = self._prepare_announcement_values(cr, uid, task)
                announcement_obj.create(cr, uid, announcement_vals)
        return True



class marketplace_announcement(osv.osv):

    _inherit = 'marketplace.announcement'

    _columns = {
        'task_id': fields.many2one('project.task', 'Task', readonly=True),
    }

    def _prepare_task_values(self, cr, uid, vals, context=None):
        partner_obj = self.pool.get('res.partner')
        partner = partner_obj.browse(cr, uid, vals['partner_id'], context=context)
        task_vals = {'name': vals['name'],'description':vals['description']}
        if partner.user_ids:
            task_vals['user_id'] = partner.user_ids[0].id
        return task_vals

    def change_state(self, cr, uid, ids, new_state, *args):
        res = super(marketplace_announcement, self).change_state(cr, uid, ids, new_state, *args)

        task_obj = self.pool.get('project.task')
        for announcement in self.browse(cr, uid, ids):
            if new_state == 'done':
                proxy = self.pool.get('ir.model.data')
                config = proxy.get_object(cr, uid, 'base_community', 'community_settings')
                if announcement.task_id:
                    task_obj.write(cr, uid, [announcement.task_id.id], {'stage_id': config.project_marketplace_stage_id.id})

        return res


    def create(self, cr, uid, vals, context=None):
        task_obj = self.pool.get('project.task')

        if not 'task_id' in vals:
            task_vals = self._prepare_task_values(cr, uid, vals, context=context)
            vals['task_id'] = task_obj.create(cr, uid, task_vals, context=context)
        res = super(marketplace_announcement, self).create(cr, uid, vals, context=context)
        #Update function fields in task
        task_obj.write(cr, uid, [vals['task_id']], {}, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        task_obj = self.pool.get('project.task')

        old_task_ids = []
        if 'task_id' in vals:
            for announcement in self.browse(cr, uid, ids, context=context):
                if announcement.task_id:
                    old_task_ids.append(announcement.task_id.id)
        res = super(marketplace_announcement, self).write(cr, uid, ids, vals, context=context)

        #Update function fields in task
        if 'task_id' in vals:
            if vals['task_id']:
                task_obj.write(cr, uid, [vals['task_id']], {}, context=context)
            if old_task_ids:
                task_obj.write(cr, uid, old_task_ids, {}, context=context)

        return res



class marketplace_proposition(osv.osv):

    _inherit = 'marketplace.proposition'

    _columns = {
        'task_id': fields.many2one('project.task', 'Task', readonly=True),
        'planned_hours': fields.float('Planned Hours'),
    }

    def _prepare_task_values(self, cr, uid, proposition, context=None):

        task_vals = {
            'name': proposition.announcement_id.name,
            'description': (proposition.announcement_id.description or '') + '\n\n=========\n\n' + (proposition.description or ''), 
            'planned_hours': proposition.planned_hours,
            'date_deadline': proposition.announcement_id.delivery_date
        }
        if proposition.announcement_id.task_id:
            task_vals['parent_ids'] = [(4,proposition.announcement_id.task_id.id)]
        if proposition.sender_id.user_ids:
            task_vals['user_id'] = proposition.sender_id.user_ids[0].id
        return task_vals

    def change_state(self, cr, uid, ids, new_state, *args):
        res = super(marketplace_proposition, self).change_state(cr, uid, ids, new_state, *args)

        task_obj = self.pool.get('project.task')
        for proposition in self.browse(cr, uid, ids): 
            if new_state == 'accepted':
                if not proposition.task_id:
                    task_vals = self._prepare_task_values(cr, uid, proposition)
                    task_id = task_obj.create(cr, uid, task_vals)
                    self.write(cr, uid, [proposition.id], {'task_id': task_id})
                    #Update function field in task
                    task_obj.write(cr, uid, [task_id], {})
            if new_state == 'paid':
                proxy = self.pool.get('ir.model.data')
                config = proxy.get_object(cr, uid, 'base_community', 'community_settings')
                if proposition.task_id:
                    task_obj.write(cr, uid, [proposition.task_id.id], {'stage_id': config.project_marketplace_stage_id.id})
                
        return res

    def write(self, cr, uid, ids, vals, context=None):
        task_obj = self.pool.get('project.task')

        old_task_ids = []
        if 'task_id' in vals:
            for proposition in self.browse(cr, uid, ids, context=context):
                if proposition.task_id:
                    old_task.append(proposition.task_id.id)
        res = super(marketplace_proposition, self).write(cr, uid, ids, vals, context=context)

        #Update function fields in task
        if 'task_id' in vals:
            if vals['task_id']:
                task_obj.write(cr, uid, [vals['task_id']], {}, context=context)
            if old_task_ids:
                task_obj.write(cr, uid, old_task_ids, {}, context=context)

        return res


class project_task_type(osv.osv):
    _inherit = 'project.task.type'

    _columns = {
        'marketplace_assignment': fields.selection([('sender','Payer'),
                                          ('receiver','Invoicer')], 'Use assignment from marketplace'),
    }


class project_assigned_user_config(osv.osv):

    _inherit = 'project.assigned.user.config'

    _columns = {
        'marketplace_assignment': fields.selection([('sender','Payer'),
                                          ('receiver','Invoicer')], 'Use assignment from marketplace'),
    }

class project_project(osv.osv):

    _inherit = 'project.project'


    def _prepare_config(self, cr, uid, id, record, vals={}, context=None):
        if 'marketplace_assignment' not in vals:
            vals['marketplace_assignment'] = 'marketplace_assignment' in record and record.marketplace_assignment or False
        _logger.info('vals prepare_config %s', vals)
        res = super(project_project, self)._prepare_config(cr, uid, id, record, vals=vals, context=context)
        return res

class project_task(osv.osv):

    _inherit = 'project.task'

    def _prepare_config(self, cr, uid, id, record, vals={}, context=None):
        if 'marketplace_assignment' not in vals:
            vals['marketplace_assignment'] = 'marketplace_assignment' in record and record.marketplace_assignment or False
        res = super(project_task, self)._prepare_config(cr, uid, id, record, vals=vals, context=context)
        return res


    def _update_assigned_user(self, cr, uid, ids, vals, context=None):
        res = super(project_task, self)._update_assigned_user(cr, uid, ids, vals, context=context)
        if 'stage_id' in vals:
            for task in self.browse(cr, uid, ids, context=context):
                for config in task.assigned_user_config_result_ids:
                    if config.stage_id.id == vals['stage_id'] and task.parent_ids and task.proposition_id and config.marketplace_assignment:
                        if config.marketplace_assignment == 'sender' and task.proposition_id.type == 'want' or config.marketplace_assignment == 'invoicer' and task.proposition_id.type == 'offer':
                            self.write(cr, uid, [task.id], {'user_id': task.parent_ids[0].user_id.id}, context=context)
                        if config.marketplace_assignment == 'sender' and task.proposition_id.type == 'offer' or config.marketplace_assignment == 'invoicer' and task.proposition_id.type == 'want' and task.proposition_id.partner_id.user_ids:
                            self.write(cr, uid, [task.id], {'user_id': task.proposition_id.partner_id.user_ids[0].id}, context=context)

        return res

