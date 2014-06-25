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
        'user_id': fields.many2one('res.users', 'Assigned user'),
    }

    def _update_assigned_user(self, cr, uid, ids, vals, context=None):
        project_obj = self.pool.get('project.project')
        if 'user_id' in vals:
            project_ids = {}
            for type in self.browse(cr, uid, ids, context=context):
                _logger.info('project_ids %s', type.project_ids)
                for project in type.project_ids:
                    project_ids[project.id] = project.id
            project_obj._update_stored_config(cr, uid, list(project_ids), context=context)


    def create(self, cr, uid, vals, context=None):
        res = super(project_task_type, self).create(cr, uid, vals, context=context)
        self._update_assigned_user(cr, uid, [res], vals, context=context)
        return res


    def write(self, cr, uid, ids, vals, context=None):
        res = super(project_task_type, self).write(cr, uid, ids, vals, context=context)
        self._update_assigned_user(cr, uid, ids, vals, context=context)
        return res



class project_assigned_user_model(osv.AbstractModel):
    ''' vote_category is meant to be inherited by any model which will define vote type
        for linked records.
    '''
    _name = 'project.assigned.user.model'
    _inherit = ['base.config.inherit.model']

    _base_config_inherit_model = 'project.assigned.user.config'
    _base_config_inherit_key = 'stage_id'
    _base_config_inherit_o2m = 'assigned_user_config_ids'

    _columns = {
        'assigned_user_config_ids': fields.one2many('project.assigned.user.config', 'res_id',
            domain=lambda self: [('model', '=', self._name),('stored','=',False)],
            auto_join=True,
            string='Assigned user configuration'),
        'assigned_user_config_result_ids': fields.one2many('project.assigned.user.config', 'res_id',
            domain=lambda self: [('model', '=', self._name),('stored','=',True)],
            auto_join=True,
            string='Assigned users', readonly=True),
    }


    def _prepare_config(self, cr, uid, id, record, vals={}, context=None):
        res = {
            'model': self._name,
            'res_id': id,
            'stage_id': 'stage_id' in record and record.stage_id.id or False,
            'user_id': 'user_id' in record and record.user_id.id or False,
            'sequence': 'sequence' in record and record.sequence or 'stage_id' in record and record.stage_id.sequence or False,
            'stored': True
        }

        res.update(super(project_assigned_user_model, self)._prepare_config(cr, uid, id, record, vals=vals, context=context))
        _logger.info('res %s', res)
        return res




class project_project(osv.osv):
    ''' vote_category is meant to be inherited by any model which will define vote type
        for linked records.
    '''

    _name = 'project.project'
    _inherit = ['project.project', 'project.assigned.user.model']

    def _get_external_config(self, cr, uid, record, context=None):
        res = {}
        for type in record.type_ids:
            if type.user_id:
                res[type.id] =  self._prepare_config(cr, uid, record.id, type, vals={'stage_id': type.id}, context=context)
        _logger.info('res %s', res)
        return res

    def _get_child_ids(self, cr, uid, ids, context=None):
        analytic_ids = {}
        for project in self.browse(cr, uid, ids, context=context):
            analytic_ids[project.analytic_account_id.id] = project.analytic_account_id.id
        return self.search(cr, uid, [('parent_id','in', list(analytic_ids))], context=context)

    def _update_stored_config_external_children(self, cr, uid, ids, context=None):
        task_obj = self.pool.get('project.task')
        task_ids = task_obj.search(cr, uid, [('project_id', 'in', ids)], context=context)
        task_obj._update_stored_config(cr, uid, task_ids, context=context)
        return True


class project_task(osv.osv):
    ''' vote_category is meant to be inherited by any model which will define vote type
        for linked records.
    '''

    _name = 'project.task'
    _inherit = ['project.task', 'project.assigned.user.model']

    def _get_external_config(self, cr, uid, record, context=None):
        res = {}
        if record.project_id:
            for config in record.project_id.assigned_user_config_result_ids:
                res[config.stage_id.id] = self._prepare_config(cr, uid, record.id, config, context=context)
        return res

    def _update_assigned_user(self, cr, uid, ids, vals, context=None):
        if 'stage_id' in vals and not 'user_id' in vals:
            for task in self.browse(cr, uid, ids, context=context):
                for config in task.assigned_user_config_result_ids:
                    if config.stage_id.id == vals['stage_id']:
                        self.write(cr, uid, [task.id], {'user_id': config.user_id.id}, context=context)

    def create(self, cr, uid, vals, context=None):
        res = super(project_task, self).create(cr, uid, vals, context=context)
        self._update_assigned_user(cr, uid, [res], vals, context=context)
        return res


    def write(self, cr, uid, ids, vals, context=None):
        res = super(project_task, self).write(cr, uid, ids, vals, context=context)
        self._update_assigned_user(cr, uid, ids, vals, context=context)
        return res


class project_assigned_user_config(osv.osv):
    _name = 'project.assigned.user.config'
    _inherit = 'base.config.inherit.line'

    _columns = {
        'stage_id': fields.many2one('project.task.type', 'Stage', required=True),
        'user_id': fields.many2one('res.users', 'Assigned User'),
    }

