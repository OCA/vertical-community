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


class vote_category(osv.AbstractModel):
    ''' vote_category is meant to be inherited by any model which will define vote type
        for linked records.
    '''
    _name = 'vote.category'
    _description = 'Vote Category'

    def _get_stored_vote_config(self, cr, uid, ids, context=None):
        vote_config_stored_obj = self.pool.get('vote.config.line.stored')

        res = {}
        for category in self.browse(cr, uid, ids, context=context):
            res[category.id] = []

            vote_config_stored_ids = vote_config_stored_obj.search(cr, uid, [('model','=',self._name),('res_id','=', category.id)], order='sequence,name', context=context)
            for vote_config_stored in vote_config_stored_obj.browse(cr, uid, vote_config_stored_ids, context=context):
                res[category.id].append(vote_config_stored) #{'name': vote_config_stored.name, 'sequence': vote_config_stored.sequence})
        return res


    def _get_vote_config(self, cr, uid, ids, field_names, arg, context=None):

        config_lines = self._get_stored_vote_config(cr, uid, ids, context=context)

        res = {}
        for category in self.browse(cr, uid, ids, context=context):
            res[category.id] = []
            for config_line in config_lines[category.id]:
                res[category.id].append((0,0,config_line))
        _logger.info('res %s',res)
        return res


    _columns = {
        'vote_config_ids': fields.one2many('vote.config.line', 'res_id',
            domain=lambda self: [('model', '=', self._name)],
            auto_join=True,
            string='Vote configuration'),
        'vote_config_result_ids': fields.one2many('vote.config.line.stored', 'res_id',
            domain=lambda self: [('model', '=', self._name)],
            auto_join=True,
            string='Vote Types', readonly=True),
    }

    def _update_stored_vote_config(self, cr, uid, ids, context=None):
        _logger.info('ids %s', ids)
        vote_config_obj = self.pool.get('vote.config.line')
        vote_config_stored_obj = self.pool.get('vote.config.line.stored')

        vote_config_stored_ids = vote_config_stored_obj.search(cr, uid, [('model','=',self._name),('res_id','in', ids)], context=context)
        vote_config_stored_obj.unlink(cr, uid, vote_config_stored_ids, context=context)

        res = {}
        for category in self.browse(cr, uid, ids, context=context):
            _logger.info('name %s', self._name)
            _logger.info('id %s', category.id)
            config_lines = {}
            if 'parent_id' in category and category.parent_id:
                for config_line in self._get_stored_vote_config(cr, uid, [category.parent_id.id], context=context)[category.parent_id.id]:
                    config_lines[config_line.name.id] = {'model': self._name, 'res_id': category.id, 'name': config_line.name.id, 'sequence': config_line.sequence}
            else:
                vote_config_ids = vote_config_obj.search(cr, uid, [('model','=','vote.config.settings'),('target_model.model','=', self._name)], context=context)
                _logger.info('vote_config_ids %s', vote_config_ids)
                for config_line in vote_config_obj.browse(cr, uid, vote_config_ids, context=context):
                    _logger.info('config.line %s', config_line.target_model.model)
                    config_lines[config_line.name.id] = {'model': self._name, 'res_id': category.id, 'name': config_line.name.id, 'sequence': config_line.sequence}

            for config_line in category.vote_config_ids:
                if config_line.action == 'add':
                    config_lines[config_line.name.id] = {'model': self._name, 'res_id': category.id, 'name': config_line.name.id, 'sequence': config_line.sequence}
                elif config_line.action == 'remove':
                    if config_line.name.id in config_lines:
                        del config_lines[config_line.name.id]


            _logger.info('config_lines %s',config_lines)
            config_lines_list = []
            for key,config_line in config_lines.iteritems():
                config_lines_list.append(config_line)

            _logger.info('config_lines %s',config_lines_list)
            sorted(config_lines_list, key = lambda config: (config['sequence'], config['name']))

            for config_line in config_lines_list:
                vote_config_stored_obj.create(cr, uid, config_line, context=context)

        if 'parent_id' in self._columns:
            child_ids = self.search(cr, uid, [('parent_id','in', ids)], context=context)
            if child_ids:
                self._update_stored_vote_config(cr, uid, child_ids, context=context)

    def create(self, cr, uid, vals, context=None):
        res = super(vote_category, self).create(cr, uid, vals, context=context)
        self.write(cr, uid, [res], vals, context=context)
        return res


    def write(self, cr, uid, ids, vals, context=None):
        res = super(vote_category, self).write(cr, uid, ids, vals, context=context)
        self._update_stored_vote_config(cr, uid, ids, context=context)
        return res
        



class vote_model(osv.AbstractModel):
    ''' vote_model is meant to be inherited by any model that needs to
        use the vote systemact as a discussion topic on which messages can be attached.

        ``vote.model`` defines fields used to handle and display the
        vote history. ``vote.model`` also manages the vote_vote field which will transparently
        fill a record in vote.vote model.
    '''
    _name = 'vote.model'
    _description = 'Vote Model'

    _vote_category_field = False
    _vote_category_model = False
    _vote_alternative_model = False
    _vote_alternative_link_field = False
    _vote_alternative_domain = False

    def _get_vote_stats(self, cr, uid, ids, name, args, context=None):
        """ Computes:
            - vote_average: Average of all vote for thi record
            - vote_total : Number of vote for this record
            - vote_user_ids : Users which have voted for this record """

        res = {}
        vote_obj = self.pool.get('vote.vote')

        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = {}
            vote_average = []
            res[record.id]['vote_average'] = 0
            res[record.id]['vote_total'] = 0
            res[record.id]['vote_user_ids'] = []
#            if self._vote_alternative_model and self._vote_alternative_link_field and self._vote_alternative_domain:
#                domain = [(self._vote_alternative_link_field, '=', record.id)] + self._vote_alternative_domain
#                record_ids = self.pool.get(self._vote_alternative_model).search(cr, uid, domain, context=context)
#                vote_ids = vote_obj.search(cr, uid, [('model','=',self._vote_alternative_model),('res_id','in',record_ids)], context=context)
#            else:
#                vote_ids = vote_obj.search(cr, uid, [('model','=',self._name),('res_id','=',record.id)], context=context)
#
#            for vote in vote_obj.browse(cr, uid, vote_ids, context=context):
#                vote_average.append(vote.vote)
#                res[record.id]['vote_total'] += 1
#                res[record.id]['vote_user_ids'].append(vote.user_id.id)

#            if len(vote_average):
#                res[record.id]['vote_average'] = sum(vote_average)/len(vote_average)
        return res

    def _get_vote_config(self, cr, uid, ids, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            _logger.info('record %s', record)
            res[record.id] = []
            if self._vote_category_field and getattr(record, self._vote_category_field):
                vote_configs = getattr(record, self._vote_category_field).vote_config_result_ids
                for vote_config in vote_configs:
                    res[record.id].append({'id': vote_config.name.id, 'name': vote_config.name.name, 'value': -3})
            else:
                vote_config_ids = vote_config_obj.search(cr, uid, [('model','=','vote.config.settings'),('target_model.model','=', self._vote_category_model or self._name)], context=context)
                for vote_config in vote_config_obj.browse(cr, uid, vote_config_ids, context=context):
                    res[record.id].append({'id': vote_config.name.id, 'name': vote_config.name.name, 'value': -3})

        return res


    def _get_vote_vote(self, cr, uid, ids, name, arg, context=None):
        """ Display the vote of the current user for the current record, if already voted """
        res = {}
        vote_obj = self.pool.get('vote.vote')
        vote_line_obj = self.pool.get('vote.vote.line')
        vote_config_obj = self.pool.get('vote.config.line')

        vote_configs = self._get_vote_config(cr, uid, ids, context=context)

        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = {}
            res[record.id]['vote_vote'] = []

            _logger.info('field %s, %s', self._vote_category_field, record)
            _logger.info('test %s',getattr(record, 'category_id'))
#            vote_config_ids = vote_config_obj.search(cr, uid, [('model','=','vote.config.settings')], context=context)
            votes = vote_configs[record.id]

            vote_lines = {}
            vote_ids = vote_obj.search(cr, uid, [('model','=',self._name),('res_id','=',record.id),('user_id','=',uid)], context=context)
            for vote in vote_obj.browse(cr, uid, vote_ids, context=context):
                res[record.id]['vote_comment'] = vote.comment
                for vote_line in vote.line_ids:
                    vote_lines[vote_line.type_id.id] = vote_line

            for vote in votes:
                if vote['id'] in vote_lines:
                    vote['value'] = vote_lines[vote['id']].vote
                res[record.id]['vote_vote'].append(vote)
        _logger.info('res : %s', res)
        return res

    def _set_vote_vote(self, cr, uid, id, name, value, arg, context=None):
        _logger.info('name : %s, value %s, arg %s', name, value, arg)

        """ Create or update the vote in vote.vote model when we save the record """
        vote_obj = self.pool.get('vote.vote')
        vote_line_obj = self.pool.get('vote.vote.line')

        vote_ids = vote_obj.search(cr, uid, [('model','=',self._name),('res_id','=',id),('user_id','=',uid)], context=context)
        vote_line_ids = vote_line_obj.search(cr, uid, [('vote_id','in',vote_ids)], context=context)
        lines = {}
        for line in vote_line_obj.browse(cr, uid, vote_line_ids, context=context):
            lines[line.type_id.id] = line
        _logger.info('lines %s', lines)
        _logger.info('value %s', value)

        if value:
            fields = {}
            if name == 'vote_comment':
                fields = {'comment': value}
            if not vote_ids:
                fields.update({'model': self._name, 'res_id': id, 'user_id': uid})
                _logger.info(fields)
                vote_id = vote_obj.create(cr, uid, fields, context=context)
            else:
                vote_obj.write(cr, uid, vote_ids, fields, context=context)
                vote_id = vote_ids[0]

            if name == 'vote_vote':
                for vote_line in value:
                    type_id = int(vote_line['type_id'])
                    if type_id in lines:
                        vote_line_obj.write(cr, uid, [lines[type_id].id], {'vote': vote_line['value']}, context=context)
                    else:
                        vote_line_obj.create(cr, uid, {'vote_id': vote_id, 'type_id': vote_line['type_id'], 'vote': vote_line['value']}, context=context)

    def clear_votes(self, cr, uid, ids, context=None):

        vote_obj = self.pool.get('vote.vote')
        vote_line_obj = self.pool.get('vote.vote.line')

        vote_ids = vote_obj.search(cr, uid, [('model','=',self._name),('res_id','in',ids)], context=context)
        vote_line_ids = vote_line_obj.search(cr, uid, [('vote_id','in',vote_ids)], context=context)
        vote_line_obj.unlink(cr, uid, vote_line_ids, context=context) 


    _columns = {
        'vote_average': fields.function(_get_vote_stats, type='float', string='Average vote', multi='_get_vote_stats'),
        'vote_total': fields.function(_get_vote_stats, type='integer', string='Total vote', multi='_get_vote_stats'),
        'vote_user_ids': fields.function(_get_vote_stats, type='many2many', obj='res.users', string='Vote users', multi='_get_vote_stats'),
        'vote_vote': fields.function(_get_vote_vote, fnct_inv=_set_vote_vote, type='char', string='Vote', multi='_get_vote_vote'),
        'vote_comment': fields.function(_get_vote_vote, fnct_inv=_set_vote_vote, type='text', string='Vote comment', multi='_get_vote_vote'),
        'vote_vote_ids': fields.one2many('vote.vote', 'res_id',
            domain=lambda self: [('model', '=', self._name)],
            auto_join=True,
            string='Votes'),
    }



class vote_vote(osv.Model):
    """ vote.vote model: Contain all votes for all objects in OpenERP """

    _name = 'vote.vote'
    _description = 'Vote'

    def _is_complete(self, cr, uid, ids, name, value, arg, context=None):
        res={}
        for vote in self.browse(cr, uid, ids, context=context):
            res[vote.id] = True

            if not vote.comment:
                res[vote.id] = False

            line_ids = {}
            for line in vote.line_ids:
                line_ids[line.type_id.id] = line.type_id.id

            model_obj = self.pool.get(vote.model)
            vote_configs = model_obj._get_vote_config(cr, uid, [vote.res_id], context=context)[vote.res_id]
            for vote_config in vote_configs:
                if vote_config['id'] not in line_ids:
                    res[vote.id] = False
        return res


    _columns = {
        'model': fields.char('Related Document Model', size=128, select=1),
        'res_id': fields.integer('Related Document ID', select=1),
        'create_date': fields.datetime('Create date'),
        'user_id': fields.many2one('res.users', 'User', select=1),
        'line_ids': fields.one2many('vote.vote.line', 'vote_id', 'Lines'),
        'comment': fields.text('Comment'),
        'is_complete': fields.function(_is_complete, type='boolean', string='Is complete?'),
    }

    _sql_constraints = [
        ('user_vote', 'unique(model,res_id,user_id)', 'We can only have one vote per record per user')
    ]



class vote_vote_line(osv.Model):
    """ vote.vote.line model: Contain all votes lines in OpenERP """

    _name = 'vote.vote.line'
    _description = 'Vote line'

    _columns = {
        'vote_id': fields.many2one('vote.vote', 'Vote', ondelete='cascade'),
        'type_id': fields.many2one('vote.type', 'Type'),
        'vote': fields.integer('Vote')
    }

    _sql_constraints = [
        ('user_vote', 'unique(vote_id,type_id)', 'We can only have one vote per vote per type')
    ]

