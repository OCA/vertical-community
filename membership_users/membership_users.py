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

from lxml import etree
from lxml.builder import E

from openerp import netsvc
from openerp import pooler
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

import logging
_logger = logging.getLogger(__name__)

class res_partner(osv.osv):

    _inherit = 'res.partner'

    _columns = {
        'presentation': fields.text('Presentation'),
    }

def name_boolean_group(id): return 'in_group_' + str(id)
def name_boolean_groups(ids): return 'in_groups_' + '_'.join(map(str, ids))
def name_selection_groups(ids): return 'sel_groups_' + '_'.join(map(str, ids))

class groups_view(osv.osv):
    _inherit = 'res.groups'

    def get_simplified_groups_by_application(self, cr, uid, context=None):
        """ return all groups classified by application (module category), as a list of pairs:
                [(app, kind, [group, ...]), ...],
            where app and group are browse records, and kind is either 'boolean' or 'selection'.
            Applications are given in sequence order.  If kind is 'selection', the groups are
            given in reverse implication order.
        """
        return []

#TODO For now we have to disable the xml_check constraint in server/openerp/addons/base/ir/ir_ui_view.py because the generated view doesn't pass the check. How the base module do it?
    def update_user_groups_view(self, cr, uid, context=None):
        res = super(groups_view, self).update_user_groups_view(cr, uid, context=context)

        _logger.info('In update_user_groups_view')
        view = self.pool['ir.model.data'].xmlid_to_object(cr, SUPERUSER_ID, 'membership_users.user_groups_view_simple_form', context=context)
        if view and view.exists() and view._name == 'ir.ui.view':
            xml1, xml2 = [], []
            xml1.append(E.separator(string=_('Access rights'), colspan="4"))
            for app, kind, gs in self.get_simplified_groups_by_application(cr, uid, context):
                attrs = {}
                if kind == 'selection':
                    # application name with a selection field
                    field_name = name_selection_groups(map(int, gs))
                    xml1.append(E.field(name=field_name, **attrs))
                    xml1.append(E.newline())
                else:
                    # application separator with boolean fields
                    app_name = app and app.name or _('Other')
                    xml2.append(E.separator(string=app_name, colspan="4", **attrs))
                    for g in gs:
                        field_name = name_boolean_group(g.id)
                        xml2.append(E.field(name=field_name, **attrs))

            xml = E.group(*(xml1 + xml2), name="group_groups_id", position="inside")
            xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY GROUPS"))
            xml_content = etree.tostring(xml, pretty_print=True, xml_declaration=True, encoding="utf-8")
            _logger.info('xml_content %s', xml_content)
            view.write({'arch': xml_content})
        return res

