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
    'name': 'Project with Groups',
    'version': '1.0',
    'category': 'Project',
    'author': 'Yannick Buron',
    'license': 'AGPL-3',
    'description': """
Project with Groups
===================

Integrate project with groups
-----------------------------
    * Project can be linked to circle, member of the circle automatically follow the project
    * Task can be assigned to role, member of the role automatically follow the task
""",
    'website': 'https://github.com/YannickB/community-management',
    'depends': [
        'mail_holacracy',
        'project_assignment',
    ],
    'data': ['project_groups_view.xml'],
    'demo': ['data/project_groups_demo.xml'],
    'test': ['tests/project_groups_test.yml'],
    'installable': True,
}
