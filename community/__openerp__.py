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

{'name': 'OpenERP CommunityTools',
 'version': '1.0',
 'category': 'Community',
 'depends': ['base',
             'calendar',
             'document',
#             'im',
             'mail_groups_holacracy',
             'membership',
             'membership_users',
             'portal',
             'website',
#             'website_livechat',
             'website_mail_group',
             ],
 'author': 'Yannick Buron',
 'license': 'AGPL-3',
 'website': 'https://launchpad.net/openerp-communitytools',
 'description': """
OpenERP for Communities
=================

This module is the base module to allow your OpenERP to manage communities. It contains the base elements and a wizard which allow you to install another features.

""",
 'data': ['community_data.xml',
          'community_view.xml',
          'security/community_security.xml',
          ],
 'demo': ['community_demo.xml'],
 'installable': True,
 'application': True,
}
