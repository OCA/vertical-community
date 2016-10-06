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
    'name': 'Marketplace for Groups',
    'version': '1.0',
    'category': 'Community',
    'author': 'Yannick Buron',
    'license': 'AGPL-3',
    'description': """
Marketplace for Groups
======================

Allow groups to make announcement and proposition
-------------------------------------------------
""",
    'website': 'https://github.com/YannickB/community-management',
    'depends': [
        'account_wallet_groups',
        'marketplace',
    ],
    'data': [
        'marketplace_groups_view.xml',
        'security/marketplace_groups_security.xml'
    ],
    'demo': ['data/marketplace_groups_demo.xml'],
    'test': [
        'tests/marketplace_groups_announcement.yml',
        'tests/marketplace_groups_rights.yml'
    ],
    'installable': True,
}
