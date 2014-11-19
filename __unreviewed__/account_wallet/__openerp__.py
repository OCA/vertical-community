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
    'name': 'Wallet and Transaction',
    'version': '1.0',
    'category': 'Accounting',
    'author': 'Yannick Buron',
    'license': 'AGPL-3',
    'description': """
Account Wallet.
===============

Allow each partners to have a wallet and make transactions between them.
------------------------------------------------------------------------
    * Transactions between partners
    * Based on accounting entries
    * Multi-currency and configurable account chart
    * Limits management
    * Display balances on the partner record, with possible
        override of limit and accounts used
""",
    'website': 'https://github.com/YannickB/community-management',
    'depends': [
            'account_accountant',
            'account_reversal',
            'base_community',
    ],
    'data': [
        'security/account_wallet_security.xml',
        'security/ir.model.access.csv',
        'account_wallet_view.xml',
        'res_config_view.xml',
        'account_wallet_workflow.xml',
        'data/account_wallet_data.xml',
    ],
    'demo': ['data/account_wallet_demo.xml'],
    'test': [
        'tests/account_wallet_users.yml',
        'tests/account_wallet_rights.yml',
        'tests/account_wallet_moderator.yml',
        'tests/account_wallet_external.yml',
        'tests/account_wallet_limits.yml',
        'tests/account_wallet_balances.yml',
    ],
    'installable': True,
}
