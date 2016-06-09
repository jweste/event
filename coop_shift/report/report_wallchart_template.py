# -*- coding: utf-8 -*-
##############################################################################
#
#    Purchase - Computed Purchase Order Module for Odoo
#    Copyright (C) 2016-Today: La Louve (<http://www.lalouve.net/>)
#    @author Julien WESTE
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
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

from openerp import api, models


class ReportWallchartTemplate(models.AbstractModel):
    _name = 'report.coop_shift.report_wallchart_template'
    _inherit = 'report.coop_shift.report_wallchart_common'

    @api.model
    def _get_tickets(self, template, product_name='Standard Subscription'):
        product_name = 'Standard Subscription'
        return super(ReportWallchartTemplate, self)._get_tickets(
            template, product_name)

    @api.multi
    def render_html(self, data):
        docargs = self.prerender_html(data)
        return self.env['report'].render(
            'coop_shift.report_wallchart_template', docargs)
