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
        begin = vals.get('date_begin', False)
        end = vals.get('date_end', False)
        res = super(ShiftTemplateRegistrationLine, self).create(vals)

        st_reg = self.env['shift.template.registration'].browse(
            vals['registration_id'])
        partner = st_reg.partner_id

        shifts = st_reg.shift_template_id.shift_ids.filtered(
            lambda s, b=begin, e=end: (s.date_begin > b or not b) and
            (s.date_end < e or not e))

        v = {
            'partner_id': partner.id,
            'state': vals['state']
        }

        sr_obj = self.env['shift.registration']
        for shift in shifts:
            ticket_id = shift.shift_ticket_ids.filtered(
                lambda t: t.product_id == st_reg.shift_ticket_id.product_id)[0]
            values = dict(v, **{
                'shift_id': shift.id,
                'shift_ticket_id': ticket_id.id,
            })
            sr_obj.create(values)
        return res

    @api.multi
    def write(self, vals):
        sr_obj = self.env['shift.registration']
        res = super(ShiftTemplateRegistrationLine, self).write(vals)
        st_reg = self.registration_id
        partner = st_reg.partner_id

        state = vals.get('state', self.state)
        begin = vals.get('date_begin', self.date_begin)
        end = vals.get('date_end', self.date_end)
        # for shifts within dates: update registration if exists, or create it
        shifts = st_reg.shift_template_id.shift_ids.filtered(
            lambda s, b=begin, e=end: (s.date_begin > b or not b) and
            (s.date_end < e or not e))
        for shift in shifts:
            found = False
            for r in shift.registration_ids:
                if r.partner_id == partner:
                    r.state = state
                    found = True
            if not found:
                ticket_id = shift.shift_ticket_ids.filtered(
                    lambda t: t.product_id ==
                    st_reg.shift_ticket_id.product_id)[0]
                values = {
                    'partner_id': partner.id,
                    'state': state,
                    'shift_id': shift.id,
                    'shift_ticket_id': ticket_id.id,
                }
                sr_obj.create(values)

        # for shifts not within dates: delete registration if exists
        shifts = st_reg.shift_template_id.shift_ids.filtered(
            lambda s, b=begin, e=end: (b and s.date_begin < b) or
            (e and s.date_end > e))
        for shift in shifts:
            for r in shift.registration_ids:
                if r.partner_id == partner:
                    r.unlink()

        return res

    @api.multi
    def unlink(self):
        for strl in self:
            partner = strl.registration_id.partner_id
            for shift in strl.registration_id.shift_template_id.shift_ids:
                for r in shift.registration_ids:
                    if r.partner_id == partner:
                        r.unlink()
        return super(ShiftTemplateRegistrationLine, self).unlink()
