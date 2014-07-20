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
#_logger = logging.getLogger(__name__)

class project_project(osv.osv):
    ''' vote_category is meant to be inherited by any model which will define vote type
        for linked records.
    '''
    _inherit = 'project.project'

    _columns = {
        'team_id': fields.many2one('mail.group', 'Team', domain=[('type','=','circle')])
    }

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

    def create(self, cr, uid, vals, context=None):
        partner_obj = self.pool.get('res.partner')
        res = super(project_task, self).create(cr, uid, vals, context=context)
        if 'assigned_partner_id' in vals:
            partner = partner_obj.browse(cr, uid, vals['assigned_partner_id'], context=context)
            if partner.group_id:
                group_obj._update_project_followers(cr, uid, [partner.group_id.id], context=context)
        return res


    def write(self, cr, uid, ids, vals, context=None):
        partner_obj = self.pool.get('res.partner')
        group_obj = self.pool.get('mail.group')
        res = super(project_task, self).write(cr, uid, ids, vals, context=context)
        if 'assigned_partner_id' in vals:
            partner = partner_obj.browse(cr, uid, vals['assigned_partner_id'], context=context)
            if partner.group_id:
                group_obj._update_project_followers(cr, uid, [partner.group_id.id], context=context)
        return res

class mail_group(osv.osv):

    _inherit = 'mail.group'

    _columns = {
        'partner_project_ids': fields.many2many('res.partner', 'mail_group_partner_projects', 'group_id', 'partner_id', 'Partners Projects', readonly=True),
    }


    def _update_project_followers(self, cr, uid, ids, context=None):
        project_obj = self.pool.get('project.project')
        task_obj = self.pool.get('project.task')
        partner_obj = self.pool.get('res.partner')

        partner_ids = []
        for g in self.browse(cr, uid, ids, context=context):
            if g.partner_id:
                partner_ids.append(g.partner_id.id)
        #_logger.info('partner_ids %s', partner_ids)
        partner_ids = [g.partner_id and g.partner_id.id for g in self.browse(cr, uid, ids, context=context)]
        #_logger.info('partner_ids %s', partner_ids)

        followers = self._get_followers(cr, uid, ids, '', '', context=context)
        #_logger.info('followers %s', followers)

        project_ids = project_obj.search(cr, uid, [('team_id', 'in', ids)], context=context)
        projects = {}
        for project in project_obj.browse(cr, uid, project_ids, context=context):
            if not project.team_id.id in projects:
                projects[project.team_id.id] = []
            projects[project.team_id.id].append(project.id)

        task_ids = task_obj.search(cr, uid, [('assigned_partner_id', 'in', partner_ids)], context=context)
        tasks = {}
        for task in task_obj.browse(cr, uid, task_ids, context=context):
            if not task.assigned_partner_id.id in tasks:
                tasks[task.assigned_partner_id.group_id.id] = []
            tasks[task.assigned_partner_id.group_id.id].append(task.id)

        #_logger.info('group project %s %s', projects, followers)
        #_logger.info('group task %s %s', tasks, followers)
        for group in self.browse(cr, uid, ids, context=context):
            if group.id in projects:
                project_obj.message_subscribe(cr, uid, projects[group.id], followers[group.id]['message_follower_ids'], context=context)
            if group.id in tasks:
                task_obj.message_subscribe(cr, uid, tasks[group.id], followers[group.id]['message_follower_ids'], context=context)
        return True

    def message_subscribe(self, cr, uid, ids, partner_ids, subtype_ids=None, context={}):
        res = super(mail_group, self).message_subscribe(cr, uid, ids, partner_ids, subtype_ids=subtype_ids, context=context)
        self._update_project_followers(cr, uid, ids, context=context)
        return res
