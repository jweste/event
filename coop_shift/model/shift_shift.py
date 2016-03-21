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

    shift_mail_ids = fields.One2many(
        'shift.mail', 'shift_id', string='Mail Schedule',
        default=lambda self: self._default_event_mail_ids())
    shift_type_id = fields.Many2one(
        'shift.type', string='Category', required=True,
        readonly=False, states={'done': [('readonly', True)]})
    registration_ids = fields.One2many(
        'shift.registration', 'shift_id', string='Attendees',
        readonly=False, states={'done': [('readonly', True)]})

    @api.model
    def _default_event_mail_ids(self):
        return super(ShiftShift, self)._default_event_mail_ids()
