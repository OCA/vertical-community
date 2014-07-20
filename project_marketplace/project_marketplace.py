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
        'announcement_creator_id': fields.many2one('res.partner', 'Who whill create the announcement?', help="If empty, the assigned partner will be used"),
        'announcement_id': fields.function(_get_marketplace, type="many2one", relation="marketplace.announcement", string="Announcement", readonly=True, multi="marketplace", store=True),
        'proposition_id': fields.function(_get_marketplace, type="many2one", relation="marketplace.proposition", string="Proposition", readonly=True, multi="marketplace", store=True),
    }

    def _prepare_announcement_values(self, cr, uid, task, context=None):
        announcement_vals = {
            'name': task.name,
            'type': 'want',
            'description':task.description,
            'task_id': task.id,
            'partner_id': task.announcement_creator_id and task.announcement_creator_id.id or task.assigned_partner_id.id
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
        'task_id': fields.many2one('project.task', 'Task'),
    }

#    def _prepare_task_values(self, cr, uid, vals, context=None):
#        partner_obj = self.pool.get('res.partner')
#        partner = partner_obj.browse(cr, uid, vals['partner_id'], context=context)
#        task_vals = {'name': vals['name'],'description':vals['description']}
#        if partner.user_ids:
#            task_vals['user_id'] = partner.user_ids[0].id
#        return task_vals

#    def change_state(self, cr, uid, ids, new_state, *args):
#        res = super(marketplace_announcement, self).change_state(cr, uid, ids, new_state, *args)
#
#        task_obj = self.pool.get('project.task')
#        for announcement in self.browse(cr, uid, ids):
#            if new_state == 'done':
#                proxy = self.pool.get('ir.model.data')
#                config = proxy.get_object(cr, uid, 'base_community', 'community_settings')
#                if announcement.task_id:
#                    task_obj.write(cr, uid, [announcement.task_id.id], {'stage_id': config.project_marketplace_stage_id.id})
#
#        return res


    def create(self, cr, uid, vals, context=None):
        task_obj = self.pool.get('project.task')

#        if not 'task_id' in vals:
#            task_vals = self._prepare_task_values(cr, uid, vals, context=context)
#            vals['task_id'] = task_obj.create(cr, uid, task_vals, context=context)
        res = super(marketplace_announcement, self).create(cr, uid, vals, context=context)
       #Update function fields in task
        if 'task_id' in vals:
            #_logger.info('task_id %s', vals['task_id'])
            task_obj.write(cr, uid, [vals['task_id']], {'assigned_partner_id': vals['partner_id']}, context=context)
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
        'task_id': fields.many2one('project.task', 'Work to do', readonly=True),
        'task_want_id': fields.many2one('project.task', 'We need your help for'),
        'planned_hours': fields.float('Planned Hours'),
    }

    def _prepare_task_values(self, cr, uid, proposition, context=None):

        task_vals = {
            'name': proposition.announcement_id.name,
            'description': (proposition.announcement_id.description or '') + '\n\n=========\n\n' + (proposition.description or ''), 
            'planned_hours': proposition.planned_hours,
            'date_deadline': proposition.announcement_id.delivery_date,
        }
        if proposition.type == 'want' and proposition.announcement_id.task_id:
            task_vals['project_id'] = proposition.announcement_id.task_id.project_id.id
            task_vals['parent_ids'] = [(6,False,[proposition.announcement_id.task_id.id])]
        if proposition.type == 'offer' and proposition.task_want_id:
            task_vals['project_id'] = proposition.task_want_id.project_id.id
            task_vals['parent_ids'] = [(6,False,[proposition.task_want_id.id])]
        if proposition.type == 'want':
            task_vals['assigned_partner_id'] = proposition.sender_id.id
            task_vals['reviewer_partner_id'] = proposition.announcement_id.partner_id.id
        else:
            task_vals['assigned_partner_id'] = proposition.announcement_id.partner_id.id
            task_vals['reviewer_partner_id'] = proposition.sender_id.id
        return task_vals

    def change_state(self, cr, uid, ids, new_state, *args):
        res = super(marketplace_proposition, self).change_state(cr, uid, ids, new_state, *args)

        task_obj = self.pool.get('project.task')
        for proposition in self.browse(cr, uid, ids): 
            if new_state == 'accepted':
                if not proposition.task_id:
                    task_vals = self._prepare_task_values(cr, uid, proposition)
                    #_logger.info('task_vals %s', task_vals)
                    parent_ids = False
                    if 'parent_ids' in task_vals:
                        parent_ids = task_vals['parent_ids']
                        del(task_vals['parent_ids'])
                    task_id = task_obj.create(cr, SUPERUSER_ID, task_vals)
                    if parent_ids:
                        #_logger.info('parent_ids proposition creation %s', parent_ids)
                        task_obj.write(cr, SUPERUSER_ID, [task_id], {'parent_ids': parent_ids})
                        #_logger.info('task parent_ids %s', task_obj.browse(cr, SUPERUSER_ID, [task_id]).parent_ids)
                    self.write(cr, SUPERUSER_ID, [proposition.id], {'task_id': task_id})
                    #Update function field in task
                    task_obj.write(cr, SUPERUSER_ID, [task_id], {'name': proposition.announcement_id.name})
#            if new_state == 'paid':
#                proxy = self.pool.get('ir.model.data')
#                config = proxy.get_object(cr, uid, 'base_community', 'community_settings')
#                if proposition.task_id:
#                    task_obj.write(cr, uid, [proposition.task_id.id], {'stage_id': config.project_marketplace_stage_id.id})
                
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
        'marketplace_assignment': fields.selection([('payer','Payer'),
                                          ('invoicer','Invoicer')], 'Use assignment from marketplace'),
    }

    def _boolean_update_projects(self, cr, uid, vals, context=None):
        res = super(project_task_type, self)._boolean_update_projects(cr, uid, vals, context=context)
        if 'marketplace_assignment' in vals:
            res = True
        return res


class project_assigned_partner_config(osv.osv):

    _inherit = 'project.assigned.partner.config'

    _columns = {
        'marketplace_assignment': fields.selection([('payer','Payer'),
                                          ('invoicer','Invoicer')], 'Use assignment from marketplace'),
    }

class project_project(osv.osv):

    _inherit = 'project.project'


    def _prepare_config(self, cr, uid, id, record, vals={}, context=None):
        name = 'name' in record and record.name or False
        if not name:
            name = self.pool.get(record.model).browse(cr, uid, record.res_id).name
        #_logger.info('vals prepare_config %s, name %s, stage %s, marketplace %s', vals, name, 'stage_id' in record and record.stage_id.name, record.marketplace_assignment)
        if 'marketplace_assignment' not in vals:
            vals['marketplace_assignment'] = 'marketplace_assignment' in record and record.marketplace_assignment or False
        #_logger.info('vals prepare_config %s', vals)
        res = super(project_project, self)._prepare_config(cr, uid, id, record, vals=vals, context=context)
        #_logger.info('vals prepare_config after %s', res)
        return res

class project_task(osv.osv):

    _inherit = 'project.task'

    def _prepare_config(self, cr, uid, id, record, vals={}, context=None):
        name = 'name' in record and record.name or False
        if not name:
            name = self.pool.get(record.model).browse(cr, uid, record.res_id).name
        #_logger.info('vals prepare_config %s, name %s, stage %s, marketplace %s', vals, name, 'stage_id' in record and record.stage_id.name, record.marketplace_assignment)
        if 'marketplace_assignment' not in vals:
            vals['marketplace_assignment'] = 'marketplace_assignment' in record and record.marketplace_assignment or False
        #_logger.info('vals prepare_config %s', vals)
        res = super(project_task, self)._prepare_config(cr, uid, id, record, vals=vals, context=context)
        #_logger.info('vals prepare_config after %s', res)
        return res


    def _update_assigned_partner(self, cr, uid, ids, vals, context=None):
        res = super(project_task, self)._update_assigned_partner(cr, uid, ids, vals, context=context)
        #_logger.info('In update vals %s, res %s', vals, res)
        if 'stage_id' in vals:
            for task in self.browse(cr, uid, ids, context=context):
                for config in task.assigned_partner_config_result_ids:
                    #_logger.info('In config %s, proposition %s, marketplace_assignment %s', config.stage_id.name, task.proposition_id, config.marketplace_assignment)
                    if config.stage_id.id == vals['stage_id'] and task.proposition_id and config.marketplace_assignment:
                        #_logger.info('Proposition ok')
                        if config.marketplace_assignment == 'payer' and task.proposition_id.type == 'want' or config.marketplace_assignment == 'invoicer' and task.proposition_id.type == 'offer':
                            partner_id = task.proposition_id.announcement_id.partner_id.id
                            if task.parent_ids and task.parent_ids[0].assigned_partner_id:
                                partner_id = task.parent_ids[0].assigned_partner_id.id
                            #_logger.info('before write announcer')
                            res['assigned_partner_id'] = partner_id
                        if config.marketplace_assignment == 'payer' and task.proposition_id.type == 'offer' or config.marketplace_assignment == 'invoicer' and task.proposition_id.type == 'want':
                            #_logger.info('before write proposer')
                            res['assigned_partner_id'] = task.proposition_id.sender_id.id

        if 'assigned_partner_id' in res:
            partner = self.pool.get('res.partner').browse(cr, uid, res['assigned_partner_id'], context=context)
            if partner.user_ids:
                res['user_id'] = partner.user_ids[0].id
            else:
                res['user_id'] = False
        #_logger.info('res project_marketplace %s', res)
        return res

