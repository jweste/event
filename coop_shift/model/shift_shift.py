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


class ShiftShift(models.Model):
    _inherit = 'event.event'
    _name = 'shift.shift'
    _description = 'Shift Template'

    @api.model
    def _default_shift_mail_ids(self):
        return [(0, 0, {
            'interval_unit': 'now',
            'interval_type': 'after_sub',
            'template_id': self.env.ref('coop_shift.shift_subscription')
        })]

    event_mail_ids = fields.One2many(default=None)
    shift_mail_ids = fields.One2many(
        'shift.mail', 'shift_id', string='Mail Schedule',
        default=lambda self: self._default_shift_mail_ids())
    shift_type_id = fields.Many2one(
        'shift.type', string='Category', required=True,
        readonly=False, states={'done': [('readonly', True)]})
    registration_ids = fields.One2many(
        'shift.registration', 'shift_id', string='Attendees',
        readonly=False, states={'done': [('readonly', True)]})
    shift_template_id = fields.Many2one('shift.template', string='Template')
    seats_reserved = fields.Integer(compute='_compute_seats_shift')
    seats_available = fields.Integer(compute='_compute_seats_shift')
    seats_unconfirmed = fields.Integer(compute='_compute_seats_shift')
    seats_used = fields.Integer(compute='_compute_seats_shift')
    seats_expected = fields.Integer(compute='_compute_seats_shift')

    @api.model
    def _default_event_mail_ids(self):
        return None

    @api.multi
    @api.depends('seats_max', 'registration_ids.state')
    def _compute_seats_shift(self):
        """ Determine reserved, available, reserved but unconfirmed and used
        seats. """
        # initialize fields to 0
        for shift in self:
            shift.seats_unconfirmed = shift.seats_reserved =\
                shift.seats_used = shift.seats_available = 0
        # aggregate registrations by shift and by state
        if self.ids:
            state_field = {
                'draft': 'seats_unconfirmed',
                'open': 'seats_reserved',
                'done': 'seats_used',
            }
            query = """ SELECT shift_id, state, count(shift_id)
                        FROM shift_registration
                        WHERE shift_id IN %s
                        AND state IN ('draft', 'open', 'done')
                        GROUP BY shift_id, state
                    """
            self._cr.execute(query, (tuple(self.ids),))
            for shift_id, state, num in self._cr.fetchall():
                shift = self.browse(shift_id)
                shift[state_field[state]] += num
        # compute seats_available
        for shift in self:
            if shift.seats_max > 0:
                shift.seats_available = shift.seats_max - (
                    shift.seats_reserved + shift.seats_used)
            shift.seats_expected = shift.seats_unconfirmed +\
                shift.seats_reserved + shift.seats_used
