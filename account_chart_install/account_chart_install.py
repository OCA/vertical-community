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

import openerp.addons.decimal_precision as dp

from openerp import netsvc
from openerp import pooler
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from datetime import datetime
import base64

import logging
_logger = logging.getLogger(__name__)


class account_chart_template(osv.osv):
    _inherit="account.chart.template"

    def install_chart(self, cr, uid, module, chart_template, company_id, currency_id, context=None):
        m = self.pool.get('ir.model.data')
        tax_templ_obj = self.pool.get('account.tax.template')
        chart = m.get_object(cr, uid, module, chart_template)

        sale_tax_ids = tax_templ_obj.search(cr, uid,
            [("chart_template_id", "=", chart.id), ('type_tax_use', 'in', ('sale','all'))],
            order="sequence, id desc")
        purchase_tax_ids = tax_templ_obj.search(cr, uid,
            [("chart_template_id", "=", chart.id), ('type_tax_use', 'in', ('purchase','all'))],
            order="sequence, id desc")
        sale_tax_rate = tax_templ_obj.browse(cr, uid, [sale_tax_ids[0]], context=context)[0].amount
        purchase_tax_rate = tax_templ_obj.browse(cr, uid, [purchase_tax_ids[0]], context=context)[0].amount

        wizard = self.pool.get('wizard.multi.charts.accounts')
        wizard_id = wizard.create(cr, uid, {
            'company_id': company_id,
            'chart_template_id': chart.id,
            'code_digits': chart.code_digits,
            'sale_tax': sale_tax_ids and sale_tax_ids[0] or False,
            'purchase_tax': purchase_tax_ids and purchase_tax_ids[0] or False,
            'sale_tax_rate': sale_tax_rate,
            'purchase_tax_rate': purchase_tax_rate,
            'complete_tax_set': chart.complete_tax_set,
            'currency_id': currency_id,
        }, context)
        wizard.execute(cr, uid, [wizard_id], context)
        return True
