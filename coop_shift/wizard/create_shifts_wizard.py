# -*- encoding: utf-8 -*-
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

from openerp import models, fields, api, _
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import UserError


class CreateShifts(models.TransientModel):
    _name = 'create.shifts.wizard'
    _description = 'Create Shifts Wizard'

    @api.model
    def _get_last_shift_date(self):
        template_id = self.env.context.get('active_id', False)
        if template_id:
            template = self.env['shift.template'].browse(template_id)
            if template.shift_ids:
                return max(
                    shift.date_begin for shift in template.shift_ids)
        return False

    @api.model
    def _get_default_date(self):
        lsd = self._get_last_shift_date()
        if lsd:
            lsd = datetime.strptime(lsd, DEFAULT_SERVER_DATETIME_FORMAT)
            return datetime.strftime(
                lsd + timedelta(days=1), DEFAULT_SERVER_DATETIME_FORMAT)
        else:
            template_id = self.env.context.get('active_id', False)
            if template_id:
                template = self.env['shift.template'].browse(template_id)
                return template.start_date
            else:
                return datetime.now()

    last_shift_date = fields.Date(
        'Last created shift date', default=_get_last_shift_date)
    date_from = fields.Date(
        'Plan this Template from', default=_get_default_date)
    date_to = fields.Date('Plan this Template until')

    @api.multi
    def create_shifts(self):
        for wizard in self:
            if wizard.date_from <= wizard.last_shift_date:
                raise UserError(_(
                    "'From date' can't be before 'Last shift date'"))
            shift_obj = self.env['shift.shift']
            registration_obj = self.env['shift.registration']
            ticket_obj = self.env['shift.ticket']
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
                    'shift_ticket_ids': None,
                }
                shift_id = shift_obj.create(vals)
                for ticket in template.shift_ticket_ids:
                    vals = {
                        'name': ticket.name,
                        'shift_id': shift_id.id,
                        'product_id': ticket.product_id.id,
                        'price': ticket.price,
                        'deadline': ticket.deadline,
                        'seats_availability': ticket.seats_availability,
                    }
                    ticket_id = ticket_obj.create(vals)

                    for attendee in ticket.registration_ids:
                        if attendee.state == "cancel":
                            pass
                        vals = {
                            'partner_id': attendee.partner_id.id,
                            'user_id': template.user_id.id,
                            'state': attendee.state,
                            'email': attendee.email,
                            'phone': attendee.phone,
                            'name': attendee.name,
                            'shift_id': shift_id.id,
                            'shift_ticket_id': ticket_id.id,
                        }
                        registration_obj.create(vals)
