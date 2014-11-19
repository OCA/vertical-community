# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Buron. Copyright Yannick Buron
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv


class VoteCategory(osv.AbstractModel):

    """
    Abstract model for vote category,
    used for specifying different vote type depending on the object category
    """

    _name = 'vote.category'
    _description = 'Feedback Category'

    _inherit = 'base.config.inherit.model'
    _base_config_inherit_model = 'vote.config.line'
    _base_config_inherit_key = 'name'
    _base_config_inherit_o2m = 'vote_config_ids'

    def _prepare_config(self, cr, uid, id, record, vals={}, context=None):
        # Specify the fields contained in the configuration
        res = {
            'model': self._name,
            'res_id': id,
            'name': 'name' in record and record.name.id or False,
            'sequence': 'sequence' in record and record.sequence or False,
            'stored': True
        }

        res.update(super(VoteCategory, self)._prepare_config(
            cr, uid, id, record, vals=vals, context=context
        ))
        return res

    _columns = {
        'vote_config_ids': fields.one2many(
            'vote.config.line', 'res_id',
            domain=lambda self: [
                ('model', '=', self._name), ('stored', '=', False)
            ], auto_join=True, string='Vote configuration'
        ),
        'vote_config_result_ids': fields.one2many(
            'vote.config.line', 'res_id',
            domain=lambda self: [
                ('model', '=', self._name), ('stored', '=', True)
            ], auto_join=True, string='Vote Types', readonly=True
        ),
    }

    def _get_external_config(self, cr, uid, record, context=None):
        # Get vote type from configuration
        res = {}
        vote_config_obj = self.pool.get('vote.config.line')
        vote_config_ids = vote_config_obj.search(
            cr, uid,
            [
                ('model', '=', 'community.config.settings'),
                ('target_model.model', '=', self._name)
            ], context=context
        )
        for config_line in vote_config_obj.browse(
                cr, uid, vote_config_ids, context=context
        ):
            res[config_line.name.id] = self._prepare_config(
                cr, uid, record.id, config_line, context=context
            )
        return res


class VoteModel(osv.AbstractModel):

    """
    Abstract class used by object which can be voted
    """

    _name = 'vote.model'
    _description = 'Vote Model'

    _vote_category_field = False
    _vote_category_model = False
    _vote_alternative_model = False
    _vote_alternative_link_field = False
    _vote_alternative_domain = False

    def _get_vote_stats(self, cr, uid, ids, name, args, context=None):
        # Return stats on the votes on this object
        res = {}

        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = {}
            res[record.id]['vote_average'] = 0
            res[record.id]['vote_total'] = 0
            res[record.id]['vote_user_ids'] = []
            #TODO
#            if self._vote_alternative_model and
# self._vote_alternative_link_field and self._vote_alternative_domain:
#                domain = [(self._vote_alternative_link_field, '=', record.id)]
#  + self._vote_alternative_domain
#                record_ids = self.pool.get(self._vote_alternative_model)
# .search(cr, uid, domain, context=context)
#                vote_ids = vote_obj.search(
#                    cr, uid, [('model','=',self._vote_alternative_model)
# ,('res_id','in',record_ids)], context=context)
#            else:
#                vote_ids = vote_obj.search(
# cr, uid, [('model','=',self._name),('res_id','=',record.id)], context=context
# )
#
#            for vote in vote_obj.browse(cr, uid, vote_ids, context=context):
#                vote_average.append(vote.vote)
#                res[record.id]['vote_total'] += 1
#                res[record.id]['vote_user_ids'].append(vote.user_id.id)

#            if len(vote_average):
#                res[record.id]['vote_average'] =
# sum(vote_average)/len(vote_average)
        return res

    def _get_vote_voters(self, cr, uid, ids, name, args, context=None):
        # Get all partner who vote on this record
        res = {}
        partner_ids = self.pool.get('res.partner').search(
            cr, uid, [('user_ids', '!=', False)], context=context
        )
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = [(6, 0, partner_ids)]
        return res

    def _get_vote_config(self, cr, uid, ids, context=None):
        # Get vote type from configuration or category
        vote_config_obj = self.pool.get('vote.config.line')
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            #_logger.info('record %s', record)
            res[record.id] = []
            if self._vote_category_field \
                    and getattr(record, self._vote_category_field):
                vote_configs = getattr(
                    record, self._vote_category_field
                ).vote_config_result_ids
                for vote_config in vote_configs:
                    res[record.id].append({
                        'id': vote_config.name.id,
                        'name': vote_config.name.name, 'value': False
                    })
            else:
                vote_config_ids = vote_config_obj.search(
                    cr, uid,
                    [
                        ('model', '=', 'community.config.settings'),
                        (
                            'target_model.model', '=',
                            self._vote_category_model or self._name
                        )
                    ], context=context
                )
                for vote_config in vote_config_obj.browse(
                        cr, uid, vote_config_ids, context=context
                ):
                    res[record.id].append({
                        'id': vote_config.name.id,
                        'name': vote_config.name.name, 'value': False
                    })

        return res

    def _get_evaluated(self, cr, uid, id, partner_id, context=None):
        # Template function which shall be overridden by inheriting
        # model to specify the object being evaluated
        res = []
        return res

    _columns = {
        'vote_average': fields.function(
            _get_vote_stats, type='float', string='Average vote',
            multi='_get_vote_stats'
        ),
        'vote_total': fields.function(
            _get_vote_stats, type='integer',
            string='Total feedback', multi='_get_vote_stats'
        ),
        'vote_user_ids': fields.function(
            _get_vote_stats, type='many2many', obj='res.users',
            string='Vote users', multi='_get_vote_stats'
        ),
        'vote_voters': fields.function(
            _get_vote_voters, type='many2many',
            obj='res.partner', string='Voters'
        ),
        'vote_vote_ids': fields.one2many(
            'vote.vote', 'res_id',
            domain=lambda self: [('model', '=', self._name)],
            auto_join=True, string='Votes'
        ),
    }


class VoteVote(osv.Model):

    """
    Object containing the vote
    """

    _name = 'vote.vote'
    _description = 'Feedback'

    def _get_lines(self, cr, uid, ids, name, value, arg, context={}):
        # Compute some field linked the lines of the vote
        res = {}
        type_obj = self.pool.get('vote.type')

        for vote in self.browse(cr, uid, ids, context=context):
            res[vote.id] = {}
            res[vote.id]['line_string'] = ''
            res[vote.id]['is_complete'] = True

            if not vote.comment:
                res[vote.id]['is_complete'] = False

            context['vote_id'] = vote.id
            for vote_line in vote.line_ids:
                type = type_obj.browse(
                    cr, uid, vote_line.type_id.id, context=context
                )
                vote_string = ''
                if vote_line.vote:
                    vote_string = vote_line.vote
                res[vote.id]['line_string'] += \
                    type.name + ' : ' + vote_string + '\n'
                if not vote_line.vote:
                    res[vote.id]['is_complete'] = False
        return res

    def _get_res_names(self, cr, uid, ids, name, value, arg, context={}):
        # Get understandable name from linked record,
        # to give some insight to the viewer of the vote
        res = {}
        model_obj = self.pool.get('ir.model')

        for vote in self.browse(cr, uid, ids, context=context):
            res[vote.id] = {}
            res[vote.id]['model_name'] = ''
            res[vote.id]['res_name'] = ''

            model_ids = model_obj.search(
                cr, uid, [('model', '=', vote.model)], context=context
            )
            for model in model_obj.browse(
                    cr, uid, model_ids, context=context
            ):
                res[vote.id]['model_name'] = model.name

            for record in self.pool.get(vote.model).browse(
                    cr, uid, [vote.res_id], context=context
            ):
                res[vote.id]['res_name'] = record.name
        return res

    _columns = {
        'model': fields.char('Related Document Model', size=128, select=1),
        'res_id': fields.integer('Related Document ID', select=1),
        'model_name': fields.function(
            _get_res_names, type="text",
            multi="_get_res_names", string="Object"
        ),
        'res_name': fields.function(
            _get_res_names, type="text",
            multi="_get_res_names", string="Name"
        ),
        'create_date': fields.datetime('Create date'),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', select=1, required=True
        ),
        'line_ids': fields.one2many('vote.vote.line', 'vote_id', 'Lines'),
        'line_string': fields.function(
            _get_lines, type="text", multi="_get_lines", string="Votes"
        ),
        'comment': fields.text('Comment'),
        'is_complete': fields.function(
            _get_lines, type='boolean',
            multi="_get_lines", string='Is complete?'
        ),
        'evaluated_object_ids': fields.many2many(
            'vote.evaluated', 'vote_vote_evaluated_rel',
            'vote_id', 'evaluated_id', 'Evaluated'
        )
    }

    def _default_line_ids(self, cr, uid, context={}):
        # Get the vote line from model config
        _logger.info('context %s', context)
        model = context.get('default_model')
        res_id = context.get('default_res_id')

        vote_lines = []
        if model and res_id:
            model_obj = self.pool.get(model)
            record = model_obj.browse(cr, uid, [res_id], context=context)
            _logger.info('record %s', record)
            if record:
                for vote_type in model_obj._get_vote_config(
                        cr, uid, [res_id], context=context
                )[res_id]:
                    _logger.info('vote_type %s', vote_type)
                    vote_lines.append((0, 0, {
                        'type_id': vote_type['id'],
                    }))
        return vote_lines

    def _default_partner(self, cr, uid, context=None):
        # Get the partner linked to the user
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        return user.partner_id.id

    _defaults = {
        'line_ids': _default_line_ids,
        'partner_id': _default_partner,
    }

    _sql_constraints = [
        (
            'user_vote', 'unique(model,res_id,partner_id)',
            'We can only have one feedback per record per partner'
        )
    ]

    def _update_evaluated(self, cr, uid, ids, context=None):
        # Update the list of evaluated record linked to this vote
        for vote in self.browse(cr, uid, ids, context=context):
            evaluated_ids = self.pool.get(vote.model)._get_evaluated(
                cr, uid, vote.res_id, vote.partner_id.id, context=context
            )
            self.write(
                cr, uid, [vote.id],
                {'evaluated_object_ids': [(6, 0, evaluated_ids)]},
                context=context
            )
        return True

    def create(self, cr, uid, vals, context=None):
        # Trigger the evaluated computation on create
        res = super(VoteVote, self).create(cr, uid, vals, context=context)
        self._update_evaluated(cr, uid, [res], context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        # Trigger the evaluated computation on write
        res = super(VoteVote, self).write(cr, uid, ids, vals, context=context)
        # Protection anti recursivity
        if not 'evaluated_object_ids' in vals:
            self._update_evaluated(cr, uid, ids, context=context)
        return res


class VoteVoteLine(osv.Model):

    """
    Vote line, containing the numeric vote for each vote type
    """

    _name = 'vote.vote.line'
    _description = 'Vote line'

    _columns = {
        'model': fields.related(
            'vote_id', 'model', type='char',
            size=128, string='Model', readonly=True, select=1
        ),
        'res_id': fields.related(
            'vote_id', 'res_id', type='integer',
            string='Related Document ID', readonly=True, select=1
        ),
        'partner_id': fields.related(
            'vote_id', 'partner_id', type='many2one',
            relation='res.partner', string='Partner', readonly=True, select=1
        ),
        'vote_id': fields.many2one('vote.vote', 'Vote', ondelete='cascade'),
        'type_id': fields.many2one('vote.type', 'Type'),
        'vote': fields.selection([('-2', '-2'),
                                  ('-1', '-1'),
                                  ('0', '0'),
                                  ('1', '1'),
                                  ('2', '2')], 'Vote')
    }

    _sql_constraints = [
        (
            'user_vote', 'unique(vote_id,type_id)',
            'You can only have one feedback per type'
        )
    ]


class VoteEvaluated(osv.Model):

    """
    Abstract class used to mark the object which can be evaluated
    """

    _name = 'vote.evaluated'

#    _columns = {
#        'vote_evaluated_ids': fields.many2many(
#            'vote.vote', 'vote_vote_evaluated_rel',
# 'evaluated_id', 'vote_id', 'Votes'
#        )
#    }


class ResPartner(osv.Model):

    """
    Mark res.partner as a evaluated class, and create the field with votes
    """

    _inherit = 'res.partner'

    _inherits = {'vote.evaluated': "vote_evaluated_id"}

    _columns = {
        'vote_evaluated_id': fields.many2one(
            'vote.evaluated', 'Evaluated',
            ondelete="cascade", required=True
        ),
        'vote_ids': fields.one2many('vote.vote', 'partner_id', 'Votes')
    }
