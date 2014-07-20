# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
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

from openerp import netsvc
from openerp import pooler
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

import logging
#_logger = logging.getLogger(__name__)

class community_module_configuration(osv.osv_memory):
    _name = 'community.module.config.settings'
    _inherit = 'res.config.settings'

    _columns = {
        'module_community_blog': fields.boolean('Install blog'),
        'module_community_crowdfunding': fields.boolean('Install crowdfunding'),
        'module_community_crm': fields.boolean('Install CRM'),
        'module_community_event': fields.boolean('Install event'),
        'module_community_forum': fields.boolean('Install forum'),
        'module_community_marketplace': fields.boolean('Install marketplace'),
        'centralbank_chart': fields.selection([('l10n_fr_centralbank','French chart of account')],string="Centralbank Chart"),
        'module_community_project': fields.boolean('Install project'),
    }

    def onchange_marketplace(self, cr, uid, ids, marketplace, context=None):
        res = {'value': {'centralbank_chart': False}}
        default = self.get_default_centralbank_chart(cr, uid, '', context=None)
        if default['centralbank_chart'] and marketplace:
            res['value']['centralbank_chart'] = default['centralbank_chart']
        return res

    def get_default_centralbank_chart(self, cr, uid, fields, context=None):
        module_obj = self.pool.get('ir.module.module')
        installed_module_ids = module_obj.search(cr, uid, [('state','in',['installed', 'to upgrade'])], context=context)
        installed_modules = []
        for module in module_obj.browse(cr, uid, installed_module_ids, context=context):
            installed_modules.append(module.name)
        res = {'centralbank_chart': False}
        if 'l10n_fr_centralbank' in installed_modules:
            res = {'centralbank_chart': 'l10n_fr_centralbank'}
        #_logger.info('res %s', res)
        return res


    def set_centralbank_chart(self, cr, uid, ids, context=None):
        #_logger.info('test set')
        ir_module = self.pool['ir.module.module']
        config = self.browse(cr, uid, ids[0], context)
        #_logger.info('centralbank %s', config.centralbank_chart)
        if config.centralbank_chart:
            module_ids = ir_module.search(cr, uid, [('name','=',config.centralbank_chart)], context=context)
            #_logger.info('module_ids %s', module_ids)
            if module_ids:
                ir_module.button_immediate_install(cr, uid, module_ids, context=context)


    def execute(self, cr, uid, ids, context=None):
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
        #_logger.info('Execute community settings, to_install %s, to_uninstall_ids %s', to_install, to_uninstall_ids)

        res = super(community_module_configuration, self).execute(cr, uid, ids, context=context)

        to_install_dependencies = []
        modules = []
        for module in to_install:
            modules.append(module[0])
        installed_module_ids = ir_module.search(cr, uid, [('state','in',['installed', 'to upgrade'])], context=context)
        installed_modules = []
        for module in ir_module.browse(cr, uid, installed_module_ids, context=context):
            installed_modules.append(module.name)
        if 'community_marketplace' in modules and 'community_project' in installed_modules or 'community_project' in modules and 'community_marketplace' in installed_modules:
            to_install_dependencies.append('project_marketplace_groups')
        if 'community_crowdfunding' in modules and 'community_project' in installed_modules or 'community_project' in modules and 'community_crowdfunding' in installed_modules:
            to_install_dependencies.append('project_crowdfunding')
        if 'community_crowdfunding' in modules and 'community_marketplace' in installed_modules or 'community_marketplace' in modules and 'community_marketplace' in installed_modules:
            to_install_dependencies.append('marketplace_crowdfunding')


        #_logger.info('to_install_dependencies %s', to_install_dependencies)
        to_install_final = []
        module_ids = ir_module.search(cr, uid, [('name','in',to_install_dependencies)], context=context)
        for module in ir_module.browse(cr, uid, module_ids, context=context):
            to_install_final.append((module.name,module))

        to_uninstall_dependencies = []
        modules = []
        for module in ir_module.browse(cr, uid, to_uninstall_ids, context=context):
            modules.append(module.name)
        #_logger.info('module uninstall %s', modules)
        if 'community_blog' in modules:
            to_uninstall_dependencies.append('website_blog')
        if 'community_crowdfunding' in modules:
            to_uninstall_dependencies.append('crowdfunding')
        if 'community_crm' in modules:
            to_uninstall_dependencies.append('crm')
        if 'community_event' in modules:
            to_uninstall_dependencies.append('event')
        if 'community_forum' in modules:
            to_uninstall_dependencies.append('website_forum')
        if 'community_marketplace' in modules:
            to_uninstall_dependencies.append('account_centralbank')
        if 'community_project' in modules:
            to_uninstall_dependencies.append('project')

        #_logger.info('to_uninstall_dependencies %s', to_uninstall_dependencies)
        to_uninstall_final_ids = []
        module_ids = ir_module.search(cr, uid, [('name','in',to_uninstall_dependencies)], context=context)
        for module in ir_module.browse(cr, uid, module_ids, context=context):
            to_uninstall_final_ids.append(module.id)

        #_logger.info('Execute community settings, to_install %s, to_uninstall_ids %s', to_install_final, to_uninstall_final_ids)
        if to_uninstall_ids:
            ir_module.button_immediate_uninstall(cr, uid, to_uninstall_final_ids, context=context)
        self._install_modules(cr, uid, to_install_final, context=context)


        return res


