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

{'name': 'Holacracy',
 'version': '1.0',
 'category': 'Social Network',
 'depends': ['base_community',
             'base_recursive_model',
             'mail',
             ],
 'author': 'Yannick Buron',
 'license': 'AGPL-3',
 'website': 'https://launchpad.net/openerp-communitytools',
 'description': """
Holacracy
=================

This module improve the mail.group object native in Odoo in order to use them as holacratic circle.
Now the group are in arborescence, you can use them as circle or role, and define access rights based on the parent and children groups.
""",
 'demo': ['data/mail_groups_holacracy_demo.xml'],
 'data': ['security/mail_groups_holacracy_security.xml',
          'security/ir.model.access.csv',
          'mail_groups_holacracy_view.xml'
          ],
 'test': ['tests/mail_groups_holacracy.yml'],
 'installable': True,
 'application': True,
}
