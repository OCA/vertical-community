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

import logging

from openerp.osv import fields, osv, ormworkflow
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class CommunityModuleConfiguration(osv.osv_memory):

    """
    Add a configuration form to install community modules
    """

    _name = 'community.module.config.settings'
    _inherit = 'res.config.settings'

    _columns = {
        'module_community_blog': fields.boolean('Install blog'),
        # 'module_community_crowdfunding': fields.boolean('Install crowdfunding'),
        'module_community_crm': fields.boolean('Install CRM'),
        'module_community_event': fields.boolean('Install event'),
        'module_community_forum': fields.boolean('Install forum'),
        'module_community_marketplace': fields.boolean('Install marketplace'),
        'wallet_chart': fields.selection([('l10n_fr_wallet', 'French chart of account')], string="Centralbank Chart"),
        'module_community_project': fields.boolean('Install project'),
    }

    def onchange_marketplace(self, cr, uid, ids, marketplace, context=None):
        # Reset wallet chart with get_default value if we change the marketplace checkbox
        res = {'value': {'wallet_chart': False}}
        default = self.get_default_wallet_chart(cr, uid, '', context=None)
        if default['wallet_chart'] and marketplace:
            res['value']['wallet_chart'] = default['wallet_chart']
        return res

    def get_default_wallet_chart(self, cr, uid, fields, context=None):
        # Get install wallet chart
        module_obj = self.pool.get('ir.module.module')
        installed_module_ids = module_obj.search(
            cr, uid, [('state', 'in', ['installed', 'to upgrade'])], context=context
        )
        installed_modules = []
        for module in module_obj.browse(cr, uid, installed_module_ids, context=context):
            installed_modules.append(module.name)
        res = {'wallet_chart': False}
        if 'l10n_fr_wallet' in installed_modules:
            res = {'wallet_chart': 'l10n_fr_wallet'}
        return res

    def set_wallet_chart(self, cr, uid, ids, context=None):
        # Install wallet chart
        ir_module = self.pool['ir.module.module']
        config = self.browse(cr, uid, ids[0], context)
        if config.wallet_chart:
            module_ids = ir_module.search(cr, uid, [('name', '=', config.wallet_chart)], context=context)
            if module_ids:
                ir_module.button_immediate_install(cr, uid, module_ids, context=context)

    def execute(self, cr, uid, ids, context=None):
        # Install or uninstall specified modules
        ir_module = self.pool['ir.module.module']
        classified = self._get_classified_fields(cr, uid, context=context)
        config = self.browse(cr, uid, ids[0], context)

        to_install = []
        to_uninstall_ids = []
        lm = len('module_')
        for name, module in classified['module']:
            if config[name]:
                to_install.append((name[lm:], module))
            else:
                if module and module.state in ('installed', 'to upgrade'):
                    to_uninstall_ids.append(module.id)

        res = super(CommunityModuleConfiguration, self).execute(cr, uid, ids, context=context)

        to_install_dependencies = []
        modules = []
        for module in to_install:
            modules.append(module[0])
        installed_module_ids = ir_module.search(
            cr, uid, [('state', 'in', ['installed', 'to upgrade'])], context=context
        )
        installed_modules = []
        for module in ir_module.browse(cr, uid, installed_module_ids, context=context):
            installed_modules.append(module.name)
        if 'community_marketplace' in modules and 'community_project' in installed_modules \
                or 'community_project' in modules and 'community_marketplace' in installed_modules:
            to_install_dependencies.append('project_marketplace')
        # if 'community_crowdfunding' in modules and 'community_project' in installed_modules \
        #         or 'community_project' in modules and 'community_crowdfunding' in installed_modules:
        #     to_install_dependencies.append('project_crowdfunding')
        # if 'community_crowdfunding' in modules and 'community_marketplace' in installed_modules \
        #         or 'community_marketplace' in modules and 'community_marketplace' in installed_modules:
        #     to_install_dependencies.append('marketplace_crowdfunding')

        to_install_final = []
        module_ids = ir_module.search(cr, uid, [('name', 'in', to_install_dependencies)], context=context)
        for module in ir_module.browse(cr, uid, module_ids, context=context):
            to_install_final.append((module.name, module))

        to_uninstall_dependencies = []
        modules = []
        for module in ir_module.browse(cr, uid, to_uninstall_ids, context=context):
            modules.append(module.name)
        if 'community_blog' in modules:
            to_uninstall_dependencies.append('website_blog')
        # if 'community_crowdfunding' in modules:
        #     to_uninstall_dependencies.append('crowdfunding')
        if 'community_crm' in modules:
            to_uninstall_dependencies.append('crm')
        if 'community_event' in modules:
            to_uninstall_dependencies.append('event')
        if 'community_forum' in modules:
            to_uninstall_dependencies.append('website_forum')
        if 'community_marketplace' in modules:
            to_uninstall_dependencies.append('account_wallet')
        if 'community_project' in modules:
            to_uninstall_dependencies.append('project')

        to_uninstall_final_ids = []
        module_ids = ir_module.search(cr, uid, [('name', 'in', to_uninstall_dependencies)], context=context)
        for module in ir_module.browse(cr, uid, module_ids, context=context):
            to_uninstall_final_ids.append(module.id)

        if to_uninstall_ids:
            ir_module.button_immediate_uninstall(cr, uid, to_uninstall_final_ids, context=context)
        self._install_modules(cr, uid, to_install_final, context=context)

        return res


