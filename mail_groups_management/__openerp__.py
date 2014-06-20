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

{'name': 'Social groups management',
 'version': '1.0',
 'category': 'Social Network',
 'depends': ['mail',
             ],
 'author': 'Yannick Buron',
 'license': 'AGPL-3',
 'website': 'https://launchpad.net/openerp-communitytools',
 'description': """
Mail groups management
=================

This module create a new group Committee which is required to create groups in social network. Groups have a management fields which indicate which people can modify this group, and specify if this group is free access or invitation only.
""",
 'demo': ['data/mail_groups_management_demo.xml'],
 'data': ['security/mail_groups_management_security.xml',
          'security/ir.model.access.csv',
          'mail_groups_management_view.xml'
          ],
 'installable': True,
 'application': True,
}
