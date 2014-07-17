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

    _inherit = 'base.config.inherit.model'
    _base_config_inherit_model = 'vote.config.line'
    _base_config_inherit_key = 'name'
    _base_config_inherit_o2m = 'vote_config_ids'

    def _prepare_config(self, cr, uid, id, record, vals={}, context=None):
        res = {
            'model': self._name,
            'res_id': id,
            'name': 'name' in record and record.name.id or False,
            'sequence': 'sequence' in record and record.sequence or False,
            'stored': True
        }

        res.update(super(vote_category, self)._prepare_config(cr, uid, id, record, vals=vals, context=context))
        return res

#    def _get_stored_vote_config(self, cr, uid, ids, context=None):
#        vote_config_stored_obj = self.pool.get('vote.config.line.stored')
#
#        res = {}
#        for category in self.browse(cr, uid, ids, context=context):
#            res[category.id] = []
#
#            vote_config_stored_ids = vote_config_stored_obj.search(cr, uid, [('model','=',self._name),('res_id','=', category.id)], order='sequence,name', context=context)
#            for vote_config_stored in vote_config_stored_obj.browse(cr, uid, vote_config_stored_ids, context=context):
#                res[category.id].append(vote_config_stored) #{'name': vote_config_stored.name, 'sequence': vote_config_stored.sequence})
#        return res


#    def _get_vote_config(self, cr, uid, ids, field_names, arg, context=None):
#
#        config_lines = self._get_stored_vote_config(cr, uid, ids, context=context)
#
#        res = {}
#        for category in self.browse(cr, uid, ids, context=context):
#            res[category.id] = []
#            for config_line in config_lines[category.id]:
#                res[category.id].append((0,0,config_line))
#        _logger.info('res %s',res)
#        return res


    _columns = {
        'vote_config_ids': fields.one2many('vote.config.line', 'res_id',
            domain=lambda self: [('model', '=', self._name),('stored','=',False)],
            auto_join=True,
            string='Vote configuration'),
        'vote_config_result_ids': fields.one2many('vote.config.line', 'res_id',
            domain=lambda self: [('model', '=', self._name),('stored','=',True)],
            auto_join=True,
            string='Vote Types', readonly=True),
    }

    def _get_external_config(self, cr, uid, record, context=None):
        res = {}
        vote_config_obj = self.pool.get('vote.config.line')
        vote_config_ids = vote_config_obj.search(cr, uid, [('model','=','community.config.settings'),('target_model.model','=', self._name)], context=context)
        _logger.info('vote_config_ids %s', vote_config_ids)
        for config_line in vote_config_obj.browse(cr, uid, vote_config_ids, context=context):
            _logger.info('config.line %s', config_line.target_model.model)
            res[config_line.name.id] =  self._prepare_config(cr, uid, record.id, config_line, context=context)
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

    def _get_vote_voters(self, cr, uid, ids, name, args, context=None):
        res = {}

        partner_ids = self.pool.get('res.partner').search(cr, uid, [('user_ids','!=',False)], context=context)
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = [(6, 0, partner_ids)]
        return res


    def _get_vote_config(self, cr, uid, ids, context=None):
        vote_config_obj = self.pool.get('vote.config.line')
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            _logger.info('record %s', record)
            res[record.id] = []
            if self._vote_category_field and getattr(record, self._vote_category_field):
                vote_configs = getattr(record, self._vote_category_field).vote_config_result_ids
                for vote_config in vote_configs:
                    res[record.id].append({'id': vote_config.name.id, 'name': vote_config.name.name, 'value': False})
            else:
                vote_config_ids = vote_config_obj.search(cr, uid, [('model','=','community.config.settings'),('target_model.model','=', self._vote_category_model or self._name)], context=context)
                for vote_config in vote_config_obj.browse(cr, uid, vote_config_ids, context=context):
                    res[record.id].append({'id': vote_config.name.id, 'name': vote_config.name.name, 'value': False})

        return res


#    def _get_vote_vote(self, cr, uid, ids, name, arg, context=None):
#        """ Display the vote of the current user for the current record, if already voted """
#        res = {}
#        vote_obj = self.pool.get('vote.vote')
#        vote_line_obj = self.pool.get('vote.vote.line')
#        vote_config_obj = self.pool.get('vote.config.line')
#
#        vote_configs = self._get_vote_config(cr, uid, ids, context=context)
#
#        for record in self.browse(cr, uid, ids, context=context):
#            res[record.id] = {}
#            res[record.id]['vote_vote'] = []
#
#            _logger.info('field %s, %s', self._vote_category_field, record)
#            _logger.info('test %s',getattr(record, 'category_id'))
#            vote_config_ids = vote_config_obj.search(cr, uid, [('model','=','vote.config.settings')], context=context)
#            votes = vote_configs[record.id]
#
#            vote_lines = {}
#            vote_ids = vote_obj.search(cr, uid, [('model','=',self._name),('res_id','=',record.id),('user_id','=',uid)], context=context)
#            for vote in vote_obj.browse(cr, uid, vote_ids, context=context):
#                res[record.id]['vote_comment'] = vote.comment
#                for vote_line in vote.line_ids:
#                    vote_lines[vote_line.type_id.id] = vote_line
#
#            for vote in votes:
#                if vote['id'] in vote_lines:
#                    vote['value'] = vote_lines[vote['id']].vote
#                res[record.id]['vote_vote'].append(vote)
#        _logger.info('res : %s', res)
#        return resi

    # def _get_partner_ids(self, cr, uid, ids, context=None):

        # res = {}
        # user_obj = self.pool.get('res.users')
        # user = user_obj.browse(cr, uid, uid, context=context)
        # partner_id = user.partner_id.id

        # for record in self.browse(cr, uid, ids, context=context):
            # res[record.id] = partner_id
        # return res




    def _get_vote_vote(self, cr, uid, ids, fields, args, context={}):

        """ Display the vote of the current user for the current record, if already voted """
        res = {}
        vote_obj = self.pool.get('vote.vote')
        vote_line_obj = self.pool.get('vote.vote.line')
        vote_config_obj = self.pool.get('vote.config.line')
        lastvoter_obj = self.pool.get('vote.last.voter')

#        partner_ids = self._get_partner_ids(cr, uid, ids, context=context)
        user_obj = self.pool.get('res.users')
        if 'vote_partner_id' in context:
            vote_partner_id = context['vote_partner_id']
        else:
            user_obj = self.pool.get('res.users')
            user = user_obj.browse(cr, uid, uid, context=context)
            vote_partner_id = user.partner_id.id
        lastvoter_obj._set_user_last_voter(cr, uid, vote_partner_id, context=context)

        vote_configs = self._get_vote_config(cr, uid, ids, context=context)

        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = {}
            res[record.id]['vote_partner_id'] = vote_partner_id
            res[record.id]['vote_comment'] = False
            res[record.id]['vote_vote_line_ids'] = []

            _logger.info('field %s, %s', self._vote_category_field, record)
            _logger.info('test %s',getattr(record, 'category_id'))
#            vote_config_ids = vote_config_obj.search(cr, uid, [('model','=','vote.config.settings')], context=context)
            votes = vote_configs[record.id]

            vote_lines = {}
            if 'vote_id' in context:
                vote_ids = [context['vote_id']]
            else:
                vote_ids = vote_obj.search(cr, uid, [('model','=',self._name),('res_id','=',record.id),('partner_id','=',vote_partner_id)], context=context)
            for vote in vote_obj.browse(cr, uid, vote_ids, context=context):
                res[record.id]['vote_comment'] = vote.comment
                for vote_line in vote.line_ids:
                    vote_lines[vote_line.type_id.id] = vote_line

            for vote in votes:
                if vote['id'] in vote_lines:
                    vote['value'] = vote_lines[vote['id']].vote
                res[record.id]['vote_vote_line_ids'].append((0,0,{'type_id':vote['id'],'vote':vote['value']}))
        _logger.info('res _get_vote_vote : %s', res)
        return res

    def _set_vote_vote(self, cr, uid, id, name, value, arg, context={}):
        _logger.info('name : %s, value %s, arg %s', name, value, arg)

        """ Create or update the vote in vote.vote model when we save the record """
        vote_obj = self.pool.get('vote.vote')
        vote_line_obj = self.pool.get('vote.vote.line')
        lastvoter_obj = self.pool.get('vote.last.voter')

        #TODO Yes I used a field in res.users to retrieve the partner specified in form... Clearly not concurrent thread proof, please tell me someone has a better idea
        if 'vote_partner_id' in context:
            vote_partner_id = context['vote_partner_id']
        else:
            vote_partner_id = lastvoter_obj.get_user_last_voter(cr, uid, context=context)

        vote_ids = vote_obj.search(cr, uid, [('model','=',self._name),('res_id','=',id),('partner_id','=',vote_partner_id)], context=context)
        vote_line_ids = vote_line_obj.search(cr, uid, [('vote_id','in',vote_ids)], context=context)
        lines = {}
        for line in vote_line_obj.browse(cr, uid, vote_line_ids, context=context):
            lines[line.type_id.id] = line
        _logger.info('lines %s', lines)
        _logger.info('value %s', value)
        _logger.info('vote_ids %s', vote_ids)

        if value:
            fields = {}
            if name == 'vote_comment':
                fields.update({'comment': value})
            if not vote_ids:
                fields.update({'model': self._name, 'res_id': id, 'partner_id': vote_partner_id})
                _logger.info('before create %s', fields)
                vote_id = vote_obj.create(cr, uid, fields, context=context)
            else:
                _logger.info('In write vote_ids %s, fields : %s', fields)
                vote_obj.write(cr, uid, vote_ids, fields, context=context)
                vote_id = vote_ids[0]

            if name == 'vote_vote_line_ids':
                vote_obj._set_lines(cr, uid, vote_id, name, value, arg, context=context)

    def onchange_vote_partner(self, cr, uid, ids, vote_partner_id, context={}):
        context['vote_partner_id'] = vote_partner_id
        votes = self._get_vote_vote(cr, uid, ids, '', '', context=context)
        _logger.info('votes %s', votes)

        res = {
            'vote_partner_id': vote_partner_id,
            'vote_comment': False,
#            'vote_vote_line_ids': False
        }
        for proposition in self.browse(cr, uid, ids, context=context):
            res = {
                'vote_partner_id': vote_partner_id,
                'vote_comment': votes[proposition.id]['vote_comment'],
#TODO
#                'vote_vote_line_ids': votes[proposition.id]['vote_vote_line_ids']
            }
        return {
            'value': res
        }

    def clear_votes(self, cr, uid, ids, context=None):

        vote_obj = self.pool.get('vote.vote')
        vote_line_obj = self.pool.get('vote.vote.line')

        vote_ids = vote_obj.search(cr, uid, [('model','=',self._name),('res_id','in',ids)], context=context)
        vote_line_ids = vote_line_obj.search(cr, uid, [('vote_id','in',vote_ids)], context=context)
        vote_line_obj.unlink(cr, uid, vote_line_ids, context=context) 

    def _get_evaluated(self, cr, uid, id, partner_id, context=None):
        res = []
        return res


    _columns = {
        'vote_average': fields.function(_get_vote_stats, type='float', string='Average vote', multi='_get_vote_stats'),
        'vote_total': fields.function(_get_vote_stats, type='integer', string='Total vote', multi='_get_vote_stats'),
        'vote_user_ids': fields.function(_get_vote_stats, type='many2many', obj='res.users', string='Vote users', multi='_get_vote_stats'),
        'vote_voters': fields.function(_get_vote_voters, type='many2many', obj='res.partner', string='Voters'),
#        'vote_vote': fields.function(_get_vote_vote, fnct_inv=_set_vote_vote, type='char', string='Vote', multi='_get_vote_vote'),
        'vote_partner_id': fields.function(_get_vote_vote, fnct_inv=_set_vote_vote, type='many2one', relation='res.partner', string='Voter', multi='_get_vote_vote'),
        'vote_comment': fields.function(_get_vote_vote, fnct_inv=_set_vote_vote, type='text', string='Vote comment', multi='_get_vote_vote'),
        'vote_vote_line_ids': fields.function(_get_vote_vote, fnct_inv=_set_vote_vote, type="one2many", relation="vote.vote.line", method=True, multi='_get_vote_vote', string='Votes'),
        'vote_vote_ids': fields.one2many('vote.vote', 'res_id',
            domain=lambda self: [('model', '=', self._name)],
            auto_join=True,
            string='Votes'),

    }



class vote_vote(osv.Model):
    """ vote.vote model: Contain all votes for all objects in OpenERP """

    _name = 'vote.vote'
    _description = 'Vote'

    def _get_lines(self, cr, uid, ids, name, value, arg, context={}):
        res={}
        type_obj = self.pool.get('vote.type')

        for vote in self.browse(cr, uid, ids, context=context):
            res[vote.id] = {}
            res[vote.id]['line_string'] = ''
            res[vote.id]['is_complete'] = True

            if not vote.comment:
                res[vote.id]['is_complete'] = False

#            line_ids = {}
#            for line in vote.line_ids:
#                line_ids[line.type_id.id] = line.type_id.id

            model_obj = self.pool.get(vote.model)
            context['vote_id'] = vote.id
            vote_lines = model_obj._get_vote_vote(cr, uid, [vote.res_id], '', '', context=context)[vote.res_id]['vote_vote_line_ids']
            _logger.info('vote %s', vote)
            res[vote.id]['vote_vote_line_ids'] = vote_lines
            for vote_line in vote_lines:
                vote_line = vote_line[2]
                type = type_obj.browse(cr, uid, vote_line['type_id'], context=context)
                vote_string = ''
                if vote_line['vote']:
                    vote_string = vote_line['vote']
                _logger.info('type %s, vote %s', type.name, vote_line['vote'])
                res[vote.id]['line_string'] += type.name + ' : ' + vote_string + '\n'
                if not vote_line['vote']:
                    res[vote.id]['is_complete'] = False

#            vote_configs = model_obj._get_vote_config(cr, uid, [vote.res_id], context=context)[vote.res_id]
#            for vote_config in vote_configs:
#                if vote_config['id'] not in line_ids:
#                    res[vote.id]['is_complete'] = False
        return res

    def _set_lines(self, cr, uid, id, name, value, arg, context=None):
        _logger.info('name : %s, value %s, arg %s', name, value, arg)
        _logger.info('!!!!!!!!!!!')
        """ Create or update the vote in vote.vote model when we save the record """
        vote_line_obj = self.pool.get('vote.vote.line')

        vote = self.browse(cr, uid, id, context=context)

        lines = {}
        for line in vote.line_ids:
            lines[line.type_id.id] = line

        if value and name == 'vote_vote_line_ids':
            _logger.info('value %s', value)
            for vote_line in value:
                vote_line = vote_line[2]
                type_id = vote_line['type_id']
                if type_id in lines:
                    vote_line_obj.write(cr, uid, [lines[type_id].id], {'vote': vote_line['vote']}, context=context)
                else:
                    vote_line_obj.create(cr, uid, {'vote_id': id, 'type_id': type_id, 'vote': vote_line['vote']}, context=context)

    def _get_voters(self, cr, uid, ids, name, value, arg, context=None):
        res = {}
        for vote in self.browse(cr, uid, ids, context=context):
            voters = self.pool.get(vote.model)._get_vote_voters(cr, uid, [vote.res_id], name, arg, context=context)[vote.res_id]
            res[vote.id] = voters
        return res

    def _get_res_names(self, cr, uid, ids, name, value, arg, context={}):
        res={}
        model_obj = self.pool.get('ir.model')

        for vote in self.browse(cr, uid, ids, context=context):
            res[vote.id] = {}
            res[vote.id]['model_name'] = ''
            res[vote.id]['res_name'] = ''

            model_ids = model_obj.search(cr, uid, [('model', '=', vote.model)], context=context)
            for model in model_obj.browse(cr, uid, model_ids, context=context):
                res[vote.id]['model_name'] = model.name

            for record in self.pool.get(vote.model).browse(cr, uid, [vote.res_id], context=context):
                res[vote.id]['res_name'] = record.name
        return res


    _columns = {
        'model': fields.char('Related Document Model', size=128, select=1),
        'res_id': fields.integer('Related Document ID', select=1),
        'model_name': fields.function(_get_res_names, type="text", multi="_get_res_names", string="Object"),
        'res_name': fields.function(_get_res_names, type="text", multi="_get_res_names", string="Name"),
        'create_date': fields.datetime('Create date'),
        'partner_id': fields.many2one('res.partner', 'Partner', select=1),
        'line_ids': fields.one2many('vote.vote.line', 'vote_id', 'Lines'),
        'line_string': fields.function(_get_lines, type="text", multi="_get_lines", string="Votes"),
        'vote_vote_line_ids': fields.function(_get_lines, fnct_inv=_set_lines, type="one2many", relation="vote.vote.line", method=True, multi='_get_lines', string='Votes'),
        'voters': fields.function(_get_voters,  type='many2many', obj='res.partner', string="Voters"),
        'comment': fields.text('Comment'),
        'is_complete': fields.function(_get_lines, type='boolean', multi="_get_lines", string='Is complete?'),
        'evaluated_object_ids': fields.many2many('vote.evaluated', 'vote_vote_evaluated_rel', 'vote_id', 'evaluated_id', 'Evaluated')
    }

    _sql_constraints = [
        ('user_vote', 'unique(model,res_id,partner_id)', 'We can only have one vote per record per partner')
    ]

    def _update_evaluated(self, cr, uid, ids, context=None):
        for vote in self.browse(cr, uid, ids, context=context):
            _logger.info('vote.model %s', vote.model)
            evaluated_ids = self.pool.get(vote.model)._get_evaluated(cr, uid, vote.res_id, vote.partner_id.id, context=context)
            _logger.info('evaluated_ids %s', evaluated_ids)
            self.write(cr, uid, [vote.id], {'evaluated_object_ids': [(6,0,evaluated_ids)]}, context=context)
            _logger.info('after')
        _logger.info('_end _update_evaluated')
        return True

    def create(self, cr, uid, vals, context=None):
        _logger.info('vals create %s', vals)
        res = super(vote_vote, self).create(cr, uid, vals, context=context)
        self._update_evaluated(cr, uid, [res], context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        
        res = super(vote_vote, self).write(cr, uid, ids, vals, context=context)
        #protection anti recursivity
        if not 'evaluated_object_ids' in vals:
            self._update_evaluated(cr, uid, ids, context=context)
        return res


class vote_vote_line(osv.Model):
    """ vote.vote.line model: Contain all votes lines in OpenERP """

    _name = 'vote.vote.line'
    _description = 'Vote line'

    _columns = {
        'vote_id': fields.many2one('vote.vote', 'Vote', ondelete='cascade'),
        'type_id': fields.many2one('vote.type', 'Type'),
        'vote': fields.selection([('-2','-2'),
                                  ('-1','-1'),
                                  ('0','0'),
                                  ('1','1'),
                                  ('2','2')],'Vote')
    }

    _sql_constraints = [
        ('user_vote', 'unique(vote_id,type_id)', 'We can only have one vote per vote per type')
    ]

class vote_evaluated(osv.Model):

    _name = 'vote.evaluated'

    _columns = {
        'vote_evaluated_ids': fields.many2many('vote.vote', 'vote_vote_evaluated_rel', 'evaluated_id', 'vote_id', 'Votes')
    }


class res_partner(osv.Model):

    _inherit = 'res.partner'

    _inherits = {'vote.evaluated': "vote_evaluated_id"}


    _columns = {
        'vote_evaluated_id': fields.many2one('vote.evaluated', 'Evaluated', ondelete="cascade", required=True),
        'vote_ids': fields.one2many('vote.vote', 'partner_id', 'Votes')
    }


class vote_last_voter(osv.Model):

    _name = 'vote.last.voter'

    _columns = {
        'user_id': fields.many2one('res.users', 'User', required=True),
        'last_voter': fields.many2one('res.partner', 'Voted last time at the name of', required=True)
    }

    def get_user_last_voter(self, cr, uid, context=None):
        lastvoter_ids = self.search(cr, uid, [('user_id','=',uid)], context=context)
        for lastvoter in self.browse(cr, uid, lastvoter_ids, context=context):
            return lastvoter.last_voter.id

        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        return user.partner_id.id

    def _set_user_last_voter(self, cr, uid, vote_partner_id, context=None):
        lastvoter_ids = self.search(cr, uid, [('user_id','=',uid)], context=context)
        lastvoter = False
        for lastvoter_temp in self.browse(cr, uid, lastvoter_ids, context=context):
            lastvoter =  lastvoter_temp

        if not lastvoter:
            self.create(cr, uid, {'user_id': uid, 'last_voter': vote_partner_id}, context=context)
        else:
            self.write(cr, uid, [lastvoter.id], {'last_voter': vote_partner_id}, context=context)


