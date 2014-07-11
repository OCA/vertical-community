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



class base_config_inherit_model(osv.AbstractModel):

    _name = 'base.config.inherit.model'

    _base_config_inherit_model = False
    _base_config_inherit_key = False
    _base_config_inherit_o2m = False

    _columns = {
        'base_config_inherit_line_del_ids': fields.one2many('base.config.inherit.line.del', 'res_id',
            domain=lambda self: [('model', '=', self._name)],
            auto_join=True,
            string='Configuration line deleted'),
    }

    def _prepare_config(self, cr, uid, id, record, vals={}, context=None):
        res = {}

        _logger.info('vals %s', vals)

        for key, value in vals.iteritems():
            res[key] = value

        return res


    def _get_external_config(self, cr, uid, record, context=None):
        _logger.info('external null')
        return {}

    def _get_child_ids(self, cr, uid, ids, context=None):
        return self.search(cr, uid, [('parent_id','in', ids)], context=context)


    def _update_stored_config_external_children(self, cr, uid, ids, context=None):
        return True


#TODO Centralize with vote object, make another module to manage this concept
    def _update_stored_config(self, cr, uid, ids, context=None):

        _logger.info('ids %s', ids)
        config_obj = self.pool.get(self._base_config_inherit_model)
        config_del_obj = self.pool.get('base.config.inherit.line.del')

        config_stored_ids = config_obj.search(cr, uid, [('model','=',self._name),('res_id','in', ids),('stored','=',True)], context=context)
        config_obj.unlink(cr, uid, config_stored_ids, context=context)
        config_del_ids = config_del_obj.search(cr, uid, [('model','=',self._name),('res_id','in', ids)], context=context)
        config_del_obj.unlink(cr, uid, config_del_ids, context=context)

        res = {}
        for record in self.browse(cr, uid, ids, context=context):

            if self._name == 'project.project':
                _logger.info('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                _logger.info('<<<<<<<<<<<<<< % <<<<<<<<<<<<<', record.id)
                _logger.info('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                _logger.info('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')


            _logger.info('name %s', self._name)
            _logger.info('id %s', record.id)
            config_lines = {}
            config_line_dels = {}

            _logger.info('before get_external')
            for key, config in self._get_external_config(cr, uid, record, context=context).iteritems():
                config_lines[key] = config
            _logger.info('after get_external')


            if 'parent_id' in record and record.parent_id:

                parent_config_del_ids = config_del_obj.search(cr, uid, [('model','=',self._name),('res_id','=', record.parent_id.id)], context=context)
                for config_line_del in config_del_obj.browse(cr, uid, parent_config_del_ids, context=context):
                    config_line_dels[config_line_del['key']] = {'model': self._name, 'res_id': record.id, 'key': config_line_del['key']}
                    if config_line_del['key'] in config_lines:
                        del config_lines[key]

                parent_config_ids = config_obj.search(cr, uid, [('model','=',self._name),('res_id','=', record.parent_id.id),('stored','=',True)], context=context)
                for config_line in config_obj.browse(cr, uid, parent_config_ids, context=context):
                    key = getattr(config_line, self._base_config_inherit_key).id
                    config_lines[key] = self._prepare_config(cr, uid, record.id, config_line, context=context)

            for config_line in getattr(record, self._base_config_inherit_o2m):
                key = getattr(config_line, self._base_config_inherit_key).id
                if config_line.action == 'add':
                    _logger.info('In add config_line %s, %s', config_line, config_line.role_id)
                    config_lines[key] = self._prepare_config(cr, uid, record.id, config_line, vals={}, context=context)
                    _logger.info('After config_line %s', config_lines)
                    if key in config_line_dels:
                        del config_line_dels[key]
                elif config_line.action == 'remove':
                    config_line_dels[key] = {'model': self._name, 'res_id': record.id, 'key': key}
                    if key in config_lines:
                        del config_lines[key]


            _logger.info('config_lines %s',config_lines)
            config_lines_list = []
            for key,config_line in config_lines.iteritems():
                config_lines_list.append(config_line)

            _logger.info('config_lines %s',config_lines_list)
            sorted(config_lines_list, key = lambda config: (config['sequence'], config[self._base_config_inherit_key]))

            for config_line in config_lines_list:
                config_obj.create(cr, uid, config_line, context=context)

            _logger.info('config_line_dels %s', config_line_dels)
            for key, config_line_del in config_line_dels.iteritems():
                _logger.info('config_line_del %s', config_line_del)
                config_del_obj.create(cr, uid, config_line_del, context=context)

        if 'parent_id' in self._columns:
            child_ids = self._get_child_ids(cr, uid, ids, context=context)
            _logger.info('-----------------------------')
            _logger.info('parent_ids %s, child_ids %s', ids, child_ids)
            _logger.info('-----------------------------')
            if child_ids:
                self._update_stored_config(cr, uid, child_ids, context=context)

        self._update_stored_config_external_children(cr, uid, ids, context=context) 

    def create(self, cr, uid, vals, context=None):
        res = super(base_config_inherit_model, self).create(cr, uid, vals, context=context)
        self._update_stored_config(cr, uid, [res], context=context)
        return res


    def write(self, cr, uid, ids, vals, context=None):
        res = super(base_config_inherit_model, self).write(cr, uid, ids, vals, context=context)
        self._update_stored_config(cr, uid, ids, context=context)
        return res


class base_config_inherit_line(osv.AbstractModel):
    _name = 'base.config.inherit.line'

    _columns = {
        'model': fields.char('Related Document Model', size=128, select=1),
        'res_id': fields.integer('Related Document ID', select=1),
        'action': fields.selection([('add','Add'),('remove','Remove')], 'Action', required=True),
        'sequence': fields.integer('Sequence'),
        'stored': fields.boolean('Stored?'),
    }

    _defaults = {
        'action': 'add'
    }

    _order = 'sequence'


class base_config_inherit_line_del(osv.osv):
    _name = 'base.config.inherit.line.del'

    _columns = {
        'model': fields.char('Related Document Model', size=128, select=1),
        'res_id': fields.integer('Related Document ID', select=1),
        'key': fields.integer('Key')
    }
