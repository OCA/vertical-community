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
    'name': 'Marketplace for project',
    'version': '1.0',
    'category': 'Community',
    'author': 'Yannick Buron',
    'license': 'AGPL-3',
    'description': """
Marketplace for Project
=======================

Link project to the marketplace
-------------------------------
    * Publish your task in the marketplace to find someone which will do it
    * When a proposition is accepted, a task is automatically created for him
    * Modify task assignment to use partner from the marketplace
""",
    'website': 'https://github.com/YannickB/community-management',
    'depends': [
        'marketplace',
        'project',
        'project_assignment'
    ],
    'data': ['project_marketplace_view.xml'],
    'demo': ['data/project_marketplace_demo.xml'],
    'test': [
        'tests/project_marketplace_want.yml',
        'tests/project_marketplace_offer.yml'
    ],
    'installable': True,
}
