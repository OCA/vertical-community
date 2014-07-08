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

{'name': 'Membership Users',
 'version': '1.0',
 'category': 'Association',
 'depends': ['membership',
             ],
 'author': 'Yannick Buron',
 'license': 'AGPL-3',
 'website': 'https://launchpad.net/openerp-communitytools',
 'description': """
Membership Users
=================

This module allow users to manage their account from association page, and moderators to manage users from the association configuration.
It also defines a membership moderator group.
""",
 'demo': [],
 'data': ['security/membership_users_security.xml',
          'security/ir.model.access.csv',
          'membership_users_view.xml'
          ],
 'installable': True,
 'application': True,
}
