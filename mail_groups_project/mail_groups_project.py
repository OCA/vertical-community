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
from operator import itemgetter

import logging
_logger = logging.getLogger(__name__)

class project_task_type(osv.osv):
    ''' vote_category is meant to be inherited by any model which will define vote type
        for linked records.
    '''
    _inherit = 'project.task.type'

    _columns = {
        'role_id': fields.many2one('mail.group', 'Assigned role', domain=[('type','=','role')]),
    }

    def _update_assigned_user(self, cr, uid, ids, vals, context=None):
        if 'role_id' in vals and not 'user_id' in vals:
            vals['user_id'] = False
        res = super(project_task_type, self)._update_assigned_user(cr, uid, ids, vals, context=context)
        return res



class project_project(osv.osv):
    ''' vote_category is meant to be inherited by any model which will define vote type
        for linked records.
    '''
    _inherit = 'project.project'

    _columns = {
        'team_id': fields.many2one('mail.group', 'Team', domain=[('type','=','circle')])
    }

    def _prepare_config(self, cr, uid, id, record, vals={}, context=None):
        _logger.info('TEST Prepare_config')
        if 'role_id' not in vals:
            vals['role_id'] = 'role_id' in record and record.role_id.id or False
        _logger.info('vals prepare_config %s', vals)
        res = super(project_project, self)._prepare_config(cr, uid, id, record, vals=vals, context=context)
        return res


    def create(self, cr, uid, vals, context=None):
        group_obj = self.pool.get('mail.group')
        res = super(project_project, self).create(cr, uid, vals, context=context)
        if 'team_id' in vals:
            group_obj._update_project_followers(cr, uid, [vals['team_id']], context=context)
        return res


    def write(self, cr, uid, ids, vals, context=None):
        group_obj = self.pool.get('mail.group')
        res = super(project_project, self).write(cr, uid, ids, vals, context=context)
        if 'team_id' in vals:
            group_obj._update_project_followers(cr, uid, [vals['team_id']], context=context)
        return res


class project_task(osv.osv):
    ''' vote_category is meant to be inherited by any model which will define vote type
        for linked records.
    '''
    _inherit = 'project.task'

    _columns = {
        'role_id': fields.many2one('mail.group', 'Assigned role', domain=[('type','=','role')]),
    }

    def _prepare_config(self, cr, uid, id, record, vals={}, context=None):
        _logger.info('TEST Prepare_config %s', record)
        if 'role_id' not in vals:
            vals['role_id'] = 'role_id' in record and record.role_id.id or False
        _logger.info('vals prepare_config %s', vals)
        res = super(project_task, self)._prepare_config(cr, uid, id, record, vals=vals, context=context)
        return res


    def _update_assigned_user(self, cr, uid, ids, vals, context=None):
        res = super(project_task, self)._update_assigned_user(cr, uid, ids, vals, context=context)
        if 'stage_id' in vals and not 'role_id' in vals:
            for task in self.browse(cr, uid, ids, context=context):
                for config in task.assigned_user_config_result_ids:
                    if config.stage_id.id == vals['stage_id'] and config.role_id:
                        self.write(cr, uid, [task.id], {'role_id': config.role_id.id}, context=context)
        return res


    def create(self, cr, uid, vals, context=None):
        group_obj = self.pool.get('mail.group')
        res = super(project_task, self).create(cr, uid, vals, context=context)
        if 'role_id' in vals:
            group_obj._update_project_followers(cr, uid, [vals['role_id']], context=context)
        return res


    def write(self, cr, uid, ids, vals, context=None):
        group_obj = self.pool.get('mail.group')
        res = super(project_task, self).write(cr, uid, ids, vals, context=context)
        if 'role_id' in vals:
            group_obj._update_project_followers(cr, uid, [vals['role_id']], context=context)
        return res


class project_assigned_user_config(osv.osv):
    _inherit = 'project.assigned.user.config'

    _columns = {
        'role_id': fields.many2one('mail.group', 'Assigned role', domain=[('type','=','role')])
    }


class mail_group(osv.osv):

    _inherit = 'mail.group'

    def _update_project_followers(self, cr, uid, ids, context=None):
        project_obj = self.pool.get('project.project')
        task_obj = self.pool.get('project.task')

        followers = self._get_followers(cr, uid, ids, '', '', context=context)
        _logger.info('followers %s', followers)

        project_ids = project_obj.search(cr, uid, [('team_id', 'in', ids)], context=context)
        projects = {}
        for project in project_obj.browse(cr, uid, project_ids, context=context):
            if not project.team_id.id in projects:
                projects[project.team_id.id] = []
            projects[project.team_id.id].append(project.id)

        task_ids = task_obj.search(cr, uid, [('role_id', 'in', ids)], context=context)
        tasks = {}
        for task in task_obj.browse(cr, uid, task_ids, context=context):
            if not task.role_id.id in tasks:
                tasks[task.role_id.id] = []
            tasks[task.role_id.id].append(task.id)

        for group in self.browse(cr, uid, ids, context=context):
            if group.id in projects:
                project_obj.message_subscribe(cr, uid, projects[group.id], followers[group.id]['message_follower_ids'], context=context)
            if group.id in tasks:
                task_obj.message_subscribe(cr, uid, tasks[group.id], followers[group.id]['message_follower_ids'], context=context)
        return True

    def message_subscribe(self, cr, uid, ids, partner_ids, subtype_ids=None, context=None):
        res = super(mail_group, self).message_subscribe(cr, uid, ids, partner_ids, subtype_ids=subtype_ids, context=context)
        self._update_project_followers(cr, uid, ids, context=context)
        return res
