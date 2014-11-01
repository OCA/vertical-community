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
    'name': 'Marketplace',
    'version': '1.0',
    'category': 'Community',
    'author': 'Yannick Buron',
    'license': 'AGPL-3',
    'description': """
Marketplace
===========

Implement a marketplace so users can exchange goods and services
----------------------------------------------------------
    * Manage announcement (Offer and Demand)
    * Make proposition with a complex acceptation and payment workflow
    * Pay in any currency available in wallet
    * Manage category and skills
""",
    'website': 'https://github.com/YannickB/community-management',
    'depends': [
        'account',
        'account_accountant',
        'account_wallet',
        'base',
        'base_recursive_model',
        'vote',
    ],
    'data': [
        'security/marketplace_security.xml',
        'security/ir.model.access.csv',
        'marketplace_view.xml',
        'marketplace_menu.xml',
        'marketplace_workflow.xml',
    ],
    'demo': ['data/marketplace_demo.xml'],
    'test': [
        'tests/marketplace_users.yml',
        'tests/marketplace_announcement.yml',
        'tests/marketplace_vote.yml',
        'tests/marketplace_rights.yml',
        'tests/marketplace_external.yml',
        'tests/marketplace_moderator.yml',
        'tests/marketplace_final.yml',
    ],
    'installable': True,
    'application': True,
}