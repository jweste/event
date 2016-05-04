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

from openerp import models, fields, api


class ShiftTemplateRegistration(models.Model):
    _inherit = 'event.registration'
    _name = 'shift.template.registration'
    _description = 'Attendee'

    event_id = fields.Many2one(required=False)
    shift_template_id = fields.Many2one(
        'shift.template', string='Template', required=True, ondelete='cascade')
    email = fields.Char(readonly=True, related='partner_id.email')
    phone = fields.Char(readonly=True, related='partner_id.phone')
    name = fields.Char(readonly=True, related='partner_id.name', store=True)
    partner_id = fields.Many2one(
        required=True, default=lambda self: self.env.user.partner_id)
    user_id = fields.Many2one(related="shift_template_id.user_id")
    shift_ticket_id = fields.Many2one(
        'shift.template.ticket', 'Shift Ticket', required=True)
    line_ids = fields.One2many(
        'shift.template.registration.line', 'registration_id', string='Lines')
    state = fields.Selection()

    _sql_constraints = [(
        'template_registration_uniq',
        'unique (shift_template_id, partner_id)',
        'This partner is already registered on this Shift Template !'),
    ]

    @api.model
    def _get_default_ticket(self):
        return self.env['shift.template'].browse(self.env.context[
            'active_id']).shift_ticket_ids[0] or False

    def _get_state(self, date_check):
        for line in self.line_ids:
            if (not line.date_begin or date_check > line.date_begin) and\
                    (not line.date_end or date_check < line.date_end):
                return line.state
        return False
