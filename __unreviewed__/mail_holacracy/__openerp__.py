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
    'name': 'Mail for Holacracy',
    'version': '1.0',
    'category': 'Social Network',
    'author': 'Yannick Buron',
    'license': 'AGPL-3',
    'description': """
Mail for Holacracy
==================

This module improve the mail.group object in order to use him for holacracy process
-----------------------------------------------------------------------------------
    * Mail.group is now a recursive model. You can't subscribe to a parent group but each followers of a group is
       automatically subscribed to his parent group
    * A group can now be a normal group, a circle or a role
    * In a circle, you can define permissions for children groups
    * A group can now be linked to a partner, you can easily create it from the group

http://en.wikipedia.org/wiki/Holacracy
""",
    'website': 'https://github.com/YannickB/community-management',
    'depends': [
        'base_community',
        'base_recursive_model',
        'mail',
    ],
    'data': [
        'security/mail_holacracy_security.xml',
        'security/ir.model.access.csv',
        'mail_holacracy_view.xml'
    ],
    'demo': ['data/mail_holacracy_demo.xml'],
    'test': ['tests/mail_holacracy.yml'],
    'installable': True,
}
