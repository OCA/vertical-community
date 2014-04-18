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

{'name': 'Vote',
 'version': '1.0',
 'category': 'Social Network',
 'depends': ['base',
             ],
 'author': 'Yannick Buron',
 'license': 'AGPL-3',
 'website': 'https://launchpad.net/vote-openerp',
 'description': """
Vote API
=================

This module provide an abstract class for your own classes, which you can use to integrate a vote system in your objects.
See marketplace module for more examples.

""",
 'demo': [],
 'data': ['security/ir.model.access.csv',
          'res_config_view.xml'],
 'installable': True,
 'application': True,
}
