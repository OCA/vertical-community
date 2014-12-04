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

from openerp.osv import fields, orm


class ProjectProject(orm.Model):

    """
    Add link between project and group
    """

    _inherit = 'project.project'

    _columns = {
        'team_id': fields.many2one(
            'mail.group', 'Team', domain=[('type', '=', 'circle')]
        )
    }

    def create(self, cr, uid, vals, context=None):
        # On create, followers of the team automatically follow the project
        group_obj = self.pool.get('mail.group')
        res = super(ProjectProject, self).create(
            cr, uid, vals, context=context
        )
        if 'team_id' in vals:
            group_obj._update_project_followers(
                cr, uid, [vals['team_id']], context=context
            )
        return res

    def write(self, cr, uid, ids, vals, context=None):
        # If we change the team, followers of the new team
        # automatically follow the project
        group_obj = self.pool.get('mail.group')
        res = super(ProjectProject, self).write(
            cr, uid, ids, vals, context=context
        )
        if 'team_id' in vals:
            group_obj._update_project_followers(
                cr, uid, [vals['team_id']], context=context
            )
        return res


class ProjectTask(orm.Model):

    """
    Add link between task and group
    """

    _inherit = 'project.task'

    def create(self, cr, uid, vals, context=None):
        # On create, if assigned parter is a group his
        # followers automatically follow the task
        partner_obj = self.pool.get('res.partner')
        group_obj = self.pool.get('mail.group')
        res = super(ProjectTask, self).create(cr, uid, vals, context=context)
        if 'assigned_partner_id' in vals:
            partner = partner_obj.browse(
                cr, uid, vals['assigned_partner_id'], context=context
            )
            if partner.group_id:
                group_obj._update_project_followers(
                    cr, uid, [partner.group_id.id], context=context
                )
        return res

    def write(self, cr, uid, ids, vals, context=None):
        # On change of assigned partner, if assigned parter
        # is a group his followers automatically follow the task
        partner_obj = self.pool.get('res.partner')
        group_obj = self.pool.get('mail.group')
        res = super(ProjectTask, self).write(
            cr, uid, ids, vals, context=context
        )
        if 'assigned_partner_id' in vals:
            partner = partner_obj.browse(
                cr, uid, vals['assigned_partner_id'], context=context
            )
            if partner.group_id:
                group_obj._update_project_followers(
                    cr, uid, [partner.group_id.id], context=context
                )
        return res


class MailGroup(orm.Model):

    _inherit = 'mail.group'

    _columns = {
        'partner_project_ids': fields.many2many(
            'res.partner', 'mail_group_partner_projects',
            'group_id', 'partner_id', 'Partners Projects', readonly=True
        ),
    }

    def _update_project_followers(self, cr, uid, ids, context=None):
        # Update followers on project and task linked
        # with the follower of the group
        project_obj = self.pool.get('project.project')
        task_obj = self.pool.get('project.task')

        partner_ids = []
        for g in self.browse(cr, uid, ids, context=context):
            if g.partner_id:
                partner_ids.append(g.partner_id.id)
        partner_ids = [g.partner_id and g.partner_id.id
                       for g in self.browse(cr, uid, ids, context=context)]

        followers = self._get_followers(cr, uid, ids, '', '', context=context)

        project_ids = project_obj.search(
            cr, uid, [('team_id', 'in', ids)], context=context
        )
        projects = {}
        for project in project_obj.browse(
                cr, uid, project_ids, context=context
        ):
            if project.team_id.id not in projects:
                projects[project.team_id.id] = []
            projects[project.team_id.id].append(project.id)

        task_ids = task_obj.search(
            cr, uid, [('assigned_partner_id', 'in', partner_ids)],
            context=context
        )
        tasks = {}
        for task in task_obj.browse(cr, uid, task_ids, context=context):
            if task.assigned_partner_id.id not in tasks:
                tasks[task.assigned_partner_id.group_id.id] = []
            tasks[task.assigned_partner_id.group_id.id].append(task.id)

        for group in self.browse(cr, uid, ids, context=context):
            if group.id in projects:
                project_obj.message_subscribe(
                    cr, uid, projects[group.id],
                    followers[group.id]['message_follower_ids'],
                    context=context
                )
            if group.id in tasks:
                task_obj.message_subscribe(
                    cr, uid, tasks[group.id],
                    followers[group.id]['message_follower_ids'],
                    context=context
                )
        return True

    def message_subscribe(
            self, cr, uid, ids, partner_ids, subtype_ids=None, context={}
    ):
        res = super(MailGroup, self).message_subscribe(
            cr, uid, ids, partner_ids,
            subtype_ids=subtype_ids, context=context
        )
        self._update_project_followers(cr, uid, ids, context=context)
        return res
