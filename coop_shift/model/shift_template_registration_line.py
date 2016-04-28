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
from openerp.exceptions import ValidationError

STATES = [
    ('cancel', 'Cancelled'),
    ('draft', 'Unconfirmed'),
    ('open', 'Confirmed'),
    ('done', 'Attended'),
    ('absent', 'Absent'),
    ('waiting', 'Waiting'),
    ('excused', 'Excused'),
    ('replaced', 'Replaced'),
    ('replacing', 'Replacing'),
]


class ShiftTemplateRegistrationLine(models.Model):
    _name = 'shift.template.registration.line'
    _description = 'Attendee Line'

    registration_id = fields.Many2one(
        'shift.template.registration', string='Registration', required=True,
        ondelete='cascade')
    date_begin = fields.Date("Begin Date")
    date_end = fields.Date("End Date")
    state = fields.Selection(STATES, string="State", default="open")

    @api.model
    def create(self, vals):
        res = super(ShiftTemplateRegistrationLine, self).create(vals)
        self._check_dates()
        return res

    @api.multi
    def write(self, vals):
        res = super(ShiftTemplateRegistrationLine, self).write(vals)
        self._check_dates()
        return res

    @api.multi
    @api.constrains()
    def _check_dates(self):
        for strl in self:
            ok = True
            registration = strl.registration_id
            for line in registration.line_ids:
                if line.date_begin and line.date_end and\
                        line.date_begin > line.date_end:
                    raise ValidationError(_(
                        """Begin date is greater than End date:"""
                        """ \n begin: %s    end: %s    state: %s;""" % (
                            line.date_begin, line.date_end, line.state)))
                for line2 in registration.line_ids:
                    if line2 == line:
                        continue
                    b1 = line.date_begin or min(
                        line.date_end, line2.date_begin, line2.date_end)
                    b2 = line2.date_begin or min(
                        line.date_begin, line.date_end, line2.date_end)
                    e1 = line.date_end or max(
                        line.date_begin, line2.date_begin, line2.date_end)
                    e2 = line2.date_end or max(
                        line.date_begin, line.date_end, line2.date_begin)
                    if b1 <= e2 and b2 <= e1:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                raise ValidationError(_(
                    """These dates overlap:"""
                    """ \n - Line1: begin: %s    end: %s    state: %s;"""
                    """ \n - Line2: begin: %s    end: %s    state: %s;""" % (
                        line.date_begin, line.date_end, line.state,
                        line2.date_begin, line2.date_end, line2.state)))
