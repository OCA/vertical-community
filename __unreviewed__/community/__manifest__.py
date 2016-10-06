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

{
    'name': 'Odoo for Communities',
    'version': '1.0',
    'category': 'Community',
    'author': 'Yannick Buron',
    'license': 'AGPL-3',
    'description': """
Odoo for Communities
====================

Use your Odoo to manage communities.
------------------------------------
    * Install official module useful for communities
    * Manage community access from user simplified form
    * Add a custom form to install module for managing community
""",
    'website': 'https://github.com/YannickB/community-management',
    'depends': [
        'base',
        'base_community',
        'calendar',
        'document',
        'gamification',
        'im_chat',
        'im_livechat',
        'mail_holacracy',
        'membership',
        'membership_users',
        'portal',
        'website',
        'website_mail_group',
    ],
    'data': [
        'data/community_data.xml',
        'community_view.xml',
        'security/community_security.xml',
        'res_config_view.xml'
    ],
    'demo': ['data/community_demo.xml'],
    'installable': True,
    'application': True,
}
