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

from openerp import models, fields


class ShiftRegistration(models.Model):
    _inherit = 'event.registration'
    _name = 'shift.registration'
    _description = 'Attendee'

    event_id = fields.Many2one(required=False)
    shift_id = fields.Many2one(
        'shift.shift', string='Shift', required=True, ondelete='cascade')
    email = fields.Char(readonly=True, related='partner_id.email')
    phone = fields.Char(readonly=True, related='partner_id.phone')
    name = fields.Char(readonly=True, related='partner_id.name', store=True)
    partner_id = fields.Many2one(
        required=True, default=lambda self: self.env.user.partner_id)
    user_id = fields.Many2one(related="shift_id.user_id")

    _sql_constraints = [(
        'shift_registration_uniq',
        'unique (shift_id, partner_id)',
        'This partner is already registered on this Shift !'),
    ]
