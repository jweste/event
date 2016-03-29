# -*- encoding: utf-8 -*-
##############################################################################
#
#    Purchase - Computed Purchase Order Module for Odoo
#    Copyright (C) 2013-Today GRAP (http://www.grap.coop)
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

from openerp import models, fields, api
from datetime import datetime, timedelta


class ShiftTemplate(models.TransientModel):
    _name = 'shift.template.wizard'
    _description = 'Shift Template Wizard'

    # @api.multi
    @api.model
    def _get_default_date(self):
        template_id = self.env.context.get('active_id', False)
        if template_id:
            return self.env['shift.template'].browse(template_id).start_date
        else:
            return datetime.now()

    date_from = fields.Date(
        'Plan this Template from', default=_get_default_date)
    date_to = fields.Date('Plan this Template until')

    @api.multi
    def create_shifts(self):
        for wizard in self:
            shift_obj = self.env['shift.shift']
            registration_obj = self.env['shift.registration']
            template_id = self.env.context.get('active_id', False)
            if not template_id:
                return
            template = self.env['shift.template'].browse(template_id)
            rec_dates = template.get_recurrent_dates(
                after=self.date_from, before=self.date_to)
            for rec_date in rec_dates:
                rec_date = datetime(
                    rec_date.year, rec_date.month, rec_date.day)
                date_begin = datetime.strftime(
                    rec_date + timedelta(hours=template.start_time),
                    "%Y-%m-%d %H:%M:%S")
                date_end = datetime.strftime(
                    rec_date + timedelta(hours=template.end_time),
                    "%Y-%m-%d %H:%M:%S")
                vals = {
                    'shift_template_id': template.id,
                    'name': template.name,
                    'user_id': template.user_id.id,
                    'company_id': template.company_id.id,
                    # 'organizer_id': template.organizer_id,
                    'seats_max': template.seats_max,
                    'seats_availability': template.seats_availability,
                    'seats_min': template.seats_min,
                    'date_tz': template.date_tz,
                    'date_begin': date_begin,
                    'date_end': date_end,
                    'state': 'draft',
                    'reply_to': template.reply_to,
                    'address_id': template.address_id.id,
                    'description': template.description,
                    'shift_type_id': template.shift_type_id.id,
                    'week_number': template.week_number,
                }
                shift_id = shift_obj.create(vals)
                for attendee in template.attendee_ids:
                    vals = {
                        'partner_id': attendee.id,
                        'state': 'draft',
                        'email': attendee.email,
                        'phone': attendee.phone,
                        'name': attendee.name,
                        'shift_id': shift_id.id,
                    }
                    registration_obj.create(vals)
