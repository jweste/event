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

import pytz
from openerp import models, fields, api, SUPERUSER_ID
from datetime import datetime


class ShiftTemplate(models.Model):
    _name = 'shift.template'
    _description = 'Shift Template'
    _order = 'shift_type_id,start_time'

    # Columns section
    name = fields.Char(
        string='Template Name', translate=True, required=True)
    active = fields.Boolean(default=True, track_visibility="onchange")
    user_id = fields.Many2one(
        'res.users', string='Shift Leader', required=True,
        default=lambda self: self.env.user)
    company_id = fields.Many2one(
        'res.company', string='Company', change_default=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'shift.shift'))
    # organizer_id = fields.Many2one(
    #     'res.partner', string='Organizer',
    #     default=lambda self: self.env.user.company_id.partner_id)
    shift_type_id = fields.Many2one(
        'shift.type', string='Category', required=True)
    color = fields.Integer('Kanban Color Index')
    shift_mail_ids = fields.One2many(
        'shift.template.mail', 'shift_template_id', string='Mail Schedule',
        default=lambda self: self._default_shift_mail_ids())
    seats_max = fields.Integer(
        string='Maximum Attendees Number',
        help="""For each shift you can define a maximum registration of
        seats(number of attendees), above this numbers the registrations
        are not accepted.""")
    seats_availability = fields.Selection(
        [('limited', 'Limited'), ('unlimited', 'Unlimited')],
        'Maximum Attendees', required=True, default='unlimited')
    seats_min = fields.Integer(
        string='Minimum Attendees', oldname='register_min',
        help="""For each shift you can define a minimum reserved seats (number
        of attendees), if it does not reach the mentioned registrations the
        shift can not be confirmed (keep 0 to ignore this rule)""")
    attendee_ids = fields.One2many(
        'shift.registration', 'shift_id', 'Attendees', ondelete='cascade')
    reply_to = fields.Char(
        'Reply-To Email',
        help="""The email address of the organizer is likely to be put here,
        with the effect to be in the 'Reply-To' of the mails sent automatically
        at shift or registrations confirmation. You can also put the email
        address of your mail gateway if you use one.""")
    address_id = fields.Many2one(
        'res.partner', string='Location',
        default=lambda self: self.env.user.company_id.partner_id,
        )
    country_id = fields.Many2one(
        'res.country', 'Country',  related='address_id.country_id', store=True)
    description = fields.Html(
        string='Description', oldname='note', translate=True,
        readonly=False,)
    date_tz = fields.Selection('_tz_get', string='Timezone',
                               default=lambda self: self.env.user.tz)
    start_date = fields.Date(string='Start Date', required=True, help="""
        First date this shift will be scheduled""")
    start_time = fields.Float(string='Start Time', required=True,)
    duration = fields.Float('Duration (hours)',)
    end_time = fields.Float(string='End Time', required=True,)

    # auto_schedule = fields.Boolean('Auto Schedule')
    # auto_confirm = fields.Boolean(
    #     string='Confirmation not required', compute='_compute_auto_confirm')

    # RECURRENCE FIELD
    rrule = fields.Char(
        compute="_get_rulestring", fnct_inv="_set_rulestring", store=True,
        string='Recurrent Rule')
    rrule_type = fields.Selection([
        ('daily', 'Day(s)'), ('weekly', 'Week(s)'), ('monthly', 'Month(s)'),
        ('yearly', 'Year(s)')], 'Recurrency', default='weekly',
        help="Let the shift automatically repeat at that interval")
    recurrency = fields.Boolean(
        'Recurrent', help="Recurrent Meeting", default=True)
    recurrent_id = fields.Integer('Recurrent ID')
    recurrent_id_date = fields.Datetime('Recurrent ID date')
    end_type = fields.Selection([
        ('count', 'Number of repetitions'), ('end_date', 'End date'),
        ('no_end', 'No end')], string='Recurrence Termination',
        default='no_end',)
    interval = fields.Integer(
        'Repeat Every', help="Repeat every (Days/Week/Month/Year)", default=4)
    count = fields.Integer('Repeat', help="Repeat x times")
    mo = fields.Boolean('Mon')
    tu = fields.Boolean('Tue')
    we = fields.Boolean('Wed')
    th = fields.Boolean('Thu')
    fr = fields.Boolean('Fri')
    sa = fields.Boolean('Sat')
    su = fields.Boolean('Sun')
    month_by = fields.Selection([
        ('date', 'Date of month'), ('day', 'Day of month')], 'Option',)
    day = fields.Integer('Date of month')
    week_list = fields.Selection([
        ('MO', 'Monday'), ('TU', 'Tuesday'), ('WE', 'Wednesday'),
        ('TH', 'Thursday'), ('FR', 'Friday'), ('SA', 'Saturday'),
        ('SU', 'Sunday')], 'Weekday')
    byday = fields.Selection([
        ('1', 'First'), ('2', 'Second'), ('3', 'Third'), ('4', 'Fourth'),
        ('5', 'Fifth'), ('-1', 'Last')], 'By day')
    final_date = fields.Date('Repeat Until')  # The last shift of a recurrence

    # Private section
    @api.model
    def _default_shift_mail_ids(self):
        return [(0, 0, {
            'interval_unit': 'now',
            'interval_type': 'after_sub',
            'template_id': self.env.ref('coop_shift.shift_subscription')
        })]

    @api.model
    def _tz_get(self):
        return [(x, x) for x in pytz.all_timezones]

    # @api.one
    # def _compute_auto_confirm(self):
    #     self.auto_confirm = self.env['ir.values'].get_default(
    #         'shift.config.settings', 'auto_confirmation')

    # def _get_rulestring(self, cr, uid, ids, name, arg, context=None):
    #     """Gets Recurrence rule string according to value type RECUR of
    #        iCalendar from the values given.
    #     @return: dictionary of rrule value.
    #     """
    #     result = {}
    #     if not isinstance(ids, list):
    #         ids = [ids]
    #     # read these fields as SUPERUSER because if the record is private a
    #     # normal search could raise an error
    #     recurrent_fields = self._get_recurrent_fields(cr, uid,
    #     context=context)
    #     shifts = self.read(
    #         cr, SUPERUSER_ID, ids, recurrent_fields, context=context)
    #     for shift in shifts:
    #         if shift['recurrency']:
    #             result[shift['id']] = self.compute_rule_string(shift)
    #         else:
    #             result[shift['id']] = ''
    #     return result

    # def _set_rulestring(
    #         self, cr, uid, ids, field_name, field_value, args, context=None):
    #     if not isinstance(ids, list):
    #         ids = [ids]
    #     data = self._get_empty_rrule_data()
    #     if field_value:
    #         data['recurrency'] = True
    #         for shift in self.browse(cr, uid, ids, context=context):
    #             rdate = shift.start
    #             update_data = self._parse_rrule(field_value, dict(data),
    #             rdate)
    #             data.update(update_data)
    #             self.write(cr, uid, ids, data, context=context)
    #     return True

    @api.onchange('duration', 'start_time')
    @api.multi
    def _compute_end_datetime(self):
        for template in self:
            if template.start_time > 24:
                template.start_time = template.start_time -\
                    24 * (template.start_time // 24)
            if template.start_time and template.duration:
                template.end_time = template.start_time + template.duration

    @api.onchange('end_time')
    @api.multi
    def _compute_duration(self):
        for template in self:
            if template.end_time > 24:
                template.end_time = template.end_time -\
                    24 * (template.end_time // 24)
            if template.start_time and template.end_time:
                template.duration = template.end_time - template.start_time

    @api.onchange('start_date')
    @api.multi
    def _onchange_start_date(self):
        for template in self:
            if template.start_date:
                start_date = datetime.strptime(template.start_date, "%Y-%m-%d")
                wd = start_date.weekday()
                template.mo = 0
                template.tu = 0
                template.we = 0
                template.th = 0
                template.fr = 0
                template.sa = 0
                template.su = 0
                if wd == 0:
                    template.mo = True
                    template.week_list = "MO"
                elif wd == 1:
                    template.tu = True
                    template.week_list = "TU"
                elif wd == 2:
                    template.we = True
                    template.week_list = "WE"
                elif wd == 3:
                    template.th = True
                    template.week_list = "TH"
                elif wd == 4:
                    template.fr = True
                    template.week_list = "FR"
                elif wd == 5:
                    template.sa = True
                    template.week_list = "SA"
                elif wd == 6:
                    template.su = True
                    template.week_list = "SU"
                template.day = start_date.day
                template.byday = "%s" % ((start_date.day - 1) // 7 + 1)
