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
    'name': 'Base Community',
    'version': '1.0',
    'category': 'Community',
    'author': 'Yannick Buron',
    'license': 'AGPL-3',
    'description': """
Base Community
==============

Create configuration menu and demo users for community modules
--------------------------------------------------------------
""",
    'website': 'https://github.com/YannickB/community-management',
    'depends': [
        'base',
        'mail'
    ],
    'data': [
        'res_config_view.xml',
        'security/ir.model.access.csv'
    ],
    'demo': ['base_community_demo.xml'],
    'installable': True,
}
