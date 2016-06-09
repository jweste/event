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
from datetime import date, datetime

rounding_limit = 0.00000000001

WEEK_DAYS = {
    'mo': 'Monday',
    'tu': 'Tuesday',
    'we': 'Wednesday',
    'th': 'Thursday',
    'fr': 'Friday',
    'sa': 'Saturday',
    'su': 'Sunday',
}


class ReportWallchartCommon(models.AbstractModel):
    _name = 'report.coop_shift.report_wallchart_common'

    @api.model
    def format_float_time(self, time):
        return '%s:%s' % (str(time).split('.')[0], int(float(str(
            '%.2f' % time).split('.')[1]) / 100 * 60) or "00")

    @api.model
    def _get_ticket_partners(self, ticket):
        partners = []
        for reg in ticket.registration_ids:
            ok = False
            dates = ""
            for line in reg.line_ids:
                if (line.date_end and datetime.strptime(
                        line.date_end, "%Y-%m-%d") <= datetime.today()) or\
                        line.state != "open":
                    continue
                ok = True
                if line.date_begin and datetime.strptime(
                        line.date_begin, "%Y-%m-%d") > datetime.today():
                    dates = ("+ from %s " % line.date_begin) + dates
                if line.date_end:
                    dates = ("+ until %s " % line.date_end) + dates
            dates = dates and (" (" + dates[2:-1] + ")")
            if ok:
                partners.append({
                    'partner_id': reg.partner_id,
                    'dates': dates})
        return partners

    @api.model
    def _get_tickets(self, template, product_name='Standard Subscription'):
        return template.shift_ticket_ids.filtered(
            lambda t: t.product_id.name == product_name)

    @api.model
    def _get_template_info(self, template):
        tickets = self._get_tickets(template)
        partners = []
        seats_max = 0
        for ticket in tickets:
            partners += self._get_ticket_partners(ticket)
            seats_max += ticket.seats_max
        return partners, seats_max

    @api.model
    def _get_templates(self, data):
        final_result = []
        for week_day in data.keys():
            if week_day == "id" or not data.get(week_day, False):
                continue

            result = []
            sql = """SELECT start_time, end_time
                FROM shift_template
                WHERE %s is True
                GROUP BY start_time, end_time
                ORDER BY start_time""" % week_day
            self.env.cr.execute(sql)

            for t in self.env.cr.fetchall():
                res = {}
                res['start_time'] = self.format_float_time(t[0])
                res['end_time'] = self.format_float_time(t[1])
                base_search = [
                    ('start_time', '>=', t[0] - rounding_limit),
                    ('start_time', '<=', t[0] + rounding_limit),
                    ('end_time', '>=', t[1] - rounding_limit),
                    ('end_time', '<=', t[1] + rounding_limit),
                ]
                week_letter = ['A', 'B', 'C', 'D']
                for week in [1, 2, 3, 4]:
                    template = self.env['shift.template'].search(
                        base_search + [('week_number', '=', week)])
                    if not template:
                        res['partners' + week_letter[week - 1]] = []
                        res['free_seats' + week_letter[week - 1]] = 0
                        continue
                    template = template[0]
                    partners, seats_max = self._get_template_info(template)
                    res['partners' + week_letter[week - 1]] = partners
                    res['free_seats' + week_letter[week - 1]] =\
                        max(0, seats_max - len(partners))
                result.append(res)
            if result:
                final_result.append({
                    'day': WEEK_DAYS[week_day],
                    'times': result
                })
        return final_result

    @api.model
    def prerender_html(self, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        wallcharts_res = self._get_templates(data['form'])

        docargs = {
            'doc_ids': self.ids,
            'partner_id': self.env.user.partner_id,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'date': date,
            'Wallcharts': wallcharts_res,
        }
        return docargs

    @api.multi
    def render_html(self, data):
        docargs = self.prerender_html(data)
        return self.env['report'].render(
            'coop_shift.report_wallchart_coin', docargs)
