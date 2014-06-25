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

{'name': 'Marketplace',
 'version': '1.0',
 'category': 'Association',
 'depends': ['base',
             'base_recursive_model',
             'account',
             'account_accountant',
             'account_reversal',
             'vote',
             ],
 'author': 'Yannick Buron',
 'license': 'AGPL-3',
 'website': 'https://launchpad.net/marketplace',
 'description': """
Marketplace
=================

""",
 'demo': [],
 'data': ['security/marketplace_security.xml',
          'security/ir.model.access.csv',
          'marketplace_view.xml',
          'marketplace_menu.xml',
          'marketplace_workflow.xml',
          'marketplace_account_data.xml',
          'res_config_view.xml',
          ],
 'installable': True,
 'application': True,
}
