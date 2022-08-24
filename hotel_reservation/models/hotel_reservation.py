# See LICENSE file for full copyright and licensing details.
import logging
from datetime import datetime, timedelta 

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt

_logger = logging.getLogger(__name__)
try:
    import pytz
except (ImportError, IOError) as err:
    _logger.debug(err)
    

class HotelReservation(models.Model):

    _name = "hotel.reservation"
    _rec_name = "reservation_no"
    _description = "Reservation"
    _order = "reservation_no desc"
    _inherit = ["mail.thread"]

    def _compute_folio_count(self):
        for res in self:
            res.update({"no_of_folio": len(res.folio_id.ids)})

    reservation_no = fields.Char("Reservation No", readonly=True, copy=False)
    date_order = fields.Datetime(
        "Date Ordered",
        readonly=True,
        required=True,
        index=True,
        default=lambda self: fields.Datetime.now(),
    )

    company_id = fields.Many2one(
        "res.company",
        "Branch",
        readonly=True,
        index=True,
        required=True,
        default=1,
        states={"draft": [("readonly", False)]},
    )
    partner_id = fields.Many2one(
        "res.partner",
        "Customer Name",
        readonly=True,
        index=True,
        required=True,
        states={"draft": [("readonly", False)]},
    )
    pricelist_id = fields.Many2one(
        "product.pricelist",
        "Scheme",
        required=True,
        states={"draft": [("readonly", False)]},
        help="Pricelist for current reservation.",
    )
    partner_invoice_id = fields.Many2one(
        "res.partner",
        "Invoice Address",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Invoice address for " "current reservation.",
    )
    partner_order_id = fields.Many2one(
        "res.partner",
        "Ordering Contact",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="The name and address of the "
        "contact that requested the order "
        "or quotation.",
    )
    partner_shipping_id = fields.Many2one(
        "res.partner",
        "Delivery Address",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Delivery address" "for current reservation. ",
    )
    checkin = fields.Datetime(
        "Start Date",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    checkout = fields.Datetime(
        "End Date",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    
    
    date_from_test = fields.Datetime("Date From", default=lambda self: fields.Date.today())
    date_to_test = fields.Datetime("Date To", default=lambda self: fields.Date.today() + relativedelta(days=30),)
    
    
    
    
    
    adults = fields.Integer(
        "Adults",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="List of adults there in guest list. ",
    )
    children = fields.Integer(
        "Children",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Number of children there in guest list.",
    )
    reservation_line = fields.One2many(
        "hotel.reservation.line",
        "line_id",
        string="Reservation Line",
        help="Hotel room reservation details.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("cancel", "Cancel"),
            ("done", "Done"),
        ],
        "State",
        readonly=True,
        default="draft",
    )
    folio_id = fields.Many2many(
        "hotel.folio",
        "hotel_folio_reservation_rel",
        "order_id",
        "invoice_id",
        string="Folio",
    )
    
    no_of_folio = fields.Integer("No. Folio", compute="_compute_folio_count")
    
    summary_header = fields.Text("Summary Header")
    room_summary = fields.Text("Room Summary")
    
    goal_rooms_test = fields.Many2many("hotel.room")
    
    
    @api.onchange("checkin")
    def on_change_checkin(self):
        self.date_from_test = self.checkin
        
          
    @api.onchange("checkout")
    def on_change_checkout(self):
        self.date_to_test = self.checkout
        
    
#     @api.onchange("goal_rooms_test")
#     def _onchange_goal_rooms_test(self):
        
#         for rec in self:
#             lines = [(5,0,0)]
#             for line in self.goal_rooms_test.name:
#                 for reservation
#                 vals = {
#                     "room_id":line.id
#                 }
#                 lines.append((0,0, vals))
#             rec.reservation_line = lines
        
        
    @api.onchange("date_from_test", "date_to_test", "reservation_line")  # noqa C901 (function is too complex)
    def get_room_summary(self):  # noqa C901 (function is too complex)
        """
        @param self: object pointer
        """
        res = {}
        all_detail = []
        room_obj = self.env["hotel.room"]
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        folio_room_line_obj = self.env["folio.room.line"]
        user_obj = self.env["res.users"]
        date_range_list = []
        main_header = []
        summary_header_list = ["Billboards"]
        if self.date_from_test and self.date_to_test:
            if self.date_from_test > self.date_to_test:
                raise UserError(_("End Date should be greater than Start date."))
            if self._context.get("tz", False):
                timezone = pytz.timezone(self._context.get("tz", False))
            else:
                timezone = pytz.timezone("UTC")
            d_frm_obj = (
                (self.date_from_test)
                .replace(tzinfo=pytz.timezone("UTC"))
                .astimezone(timezone)
            )
            d_to_obj = (
                (self.date_to_test).replace(tzinfo=pytz.timezone("UTC")).astimezone(timezone)
            )
            temp_date = d_frm_obj
            while temp_date <= d_to_obj:
                val = ""
                val = (
                    str(temp_date.strftime("%a"))
                    + " "
                    + str(temp_date.strftime("%b"))
                    + " "
                    + str(temp_date.strftime("%d"))
                )
                summary_header_list.append(val)
                date_range_list.append(temp_date.strftime(dt))
                temp_date = temp_date + timedelta(days=1)
            all_detail.append(summary_header_list)
            room_ids = room_obj.search([])
            all_room_detail = []
            for rec in self.reservation_line:
                for room in room_ids:
                    for reservation in rec.reserve:
                        if reservation.name == room.name:
                        
                            room_detail = {}
                            room_list_stats = []
                            room_detail.update({"name": room.name or ""})
                            if not room.room_reservation_line_ids and not room.room_line_ids:
                                for chk_date in date_range_list:
                                    room_list_stats.append(
                                        {
                                            "state": "Free",
                                            "date": chk_date,
                                            "room_id": room.id,
                                        }
                                    )
                            else:
                                for chk_date in date_range_list:
                                    ch_dt = chk_date[:10] + " 23:59:59"
                                    ttime = datetime.strptime(ch_dt, dt)
                                    c = ttime.replace(tzinfo=timezone).astimezone(
                                        pytz.timezone("UTC")
                                    )
                                    chk_date = c.strftime(dt)
                                    reserline_ids = room.room_reservation_line_ids.ids
                                    reservline_ids = reservation_line_obj.search(
                                        [
                                            ("id", "in", reserline_ids),
                                            ("check_in", "<=", chk_date),
                                            ("check_out", ">=", chk_date),
                                            ("state", "=", "assigned"),
                                        ]
                                    )
                                    if not reservline_ids:
                                        sdt = dt
                                        chk_date = datetime.strptime(chk_date, sdt)
                                        chk_date = datetime.strftime(
                                            chk_date - timedelta(days=1), sdt
                                        )
                                        reservline_ids = reservation_line_obj.search(
                                            [
                                                ("id", "in", reserline_ids),
                                                ("check_in", "<=", chk_date),
                                                ("check_out", ">=", chk_date),
                                                ("state", "=", "assigned"),
                                            ]
                                        )
                                        for res_room in reservline_ids:
                                            cid = res_room.check_in
                                            cod = res_room.check_out
                                            dur = cod - cid
                                            if room_list_stats:
                                                count = 0
                                                for rlist in room_list_stats:
                                                    cidst = datetime.strftime(cid, dt)
                                                    codst = datetime.strftime(cod, dt)
                                                    rm_id = res_room.room_id.id
                                                    ci = rlist.get("date") >= cidst
                                                    co = rlist.get("date") <= codst
                                                    rm = rlist.get("room_id") == rm_id
                                                    st = rlist.get("state") == "Reserved"
                                                    if ci and co and rm and st:
                                                        count += 1
                                                if count - dur.days == 0:
                                                    c_id1 = user_obj.browse(self._uid)
                                                    c_id = c_id1.company_id
                                                    con_add = 0
                                                    amin = 0.0
                                                    # When configured_addition_hours is
                                                    # greater than zero then we calculate
                                                    # additional minutes
                                                    if c_id:
                                                        con_add = c_id.additional_hours
                                                    if con_add > 0:
                                                        amin = abs(con_add * 60)
                                                    hr_dur = abs(dur.seconds / 60)
                                                    if amin > 0:
                                                        # When additional minutes is greater
                                                        # than zero then check duration with
                                                        # extra minutes and give the room
                                                        # reservation status is reserved
                                                        # --------------------------
                                                        if hr_dur >= amin:
                                                            reservline_ids = True
                                                        else:
                                                            reservline_ids = False
                                                    else:
                                                        if hr_dur > 0:
                                                            reservline_ids = True
                                                        else:
                                                            reservline_ids = False
                                                else:
                                                    reservline_ids = False
                                    fol_room_line_ids = room.room_line_ids.ids
                                    chk_state = ["draft", "cancel"]
                                    folio_resrv_ids = folio_room_line_obj.search(
                                        [
                                            ("id", "in", fol_room_line_ids),
                                            ("check_in", "<=", chk_date),
                                            ("check_out", ">=", chk_date),
                                            ("status", "not in", chk_state),
                                        ]
                                    )
                                    if reservline_ids or folio_resrv_ids:
                                        room_list_stats.append(
                                            {
                                                "state": "Reserved",
                                                "date": chk_date,
                                                "room_id": room.id,
                                                "is_draft": "No",
                                                "data_model": "",
                                                "data_id": 0,
                                            }
                                        )
                                    else:
                                        room_list_stats.append(
                                            {
                                                "state": "Free",
                                                "date": chk_date,
                                                "room_id": room.id,
                                            }
                                        )

                            room_detail.update({"value": room_list_stats})
                            all_room_detail.append(room_detail)
            main_header.append({"header": summary_header_list})
            self.summary_header = str(main_header)
            self.room_summary = str(all_room_detail)
        return res
    
        

#     def unlink(self):
#         """
#         Overrides orm unlink method.
#         @param self: The object pointer
#         @return: True/False.
#         """
#         lines_of_moves_to_post = self.filtered(
#             lambda reserv_rec: reserv_rec.state != "draft"
#         )
#         if lines_of_moves_to_post:
#             raise ValidationError(
#                 _("Sorry, you can only delete the reservation when it's draft!")
#             )
#         return super(HotelReservation, self).unlink()

    def copy(self):
        ctx = dict(self._context) or {}
        ctx.update({"duplicate": True})
        return super(HotelReservation, self.with_context(ctx)).copy()

#     @api.constrains("reservation_line", "adults", "children")
#     def _check_reservation_rooms(self):
#         """
#         This method is used to validate the reservation_line.
#         -----------------------------------------------------
#         @param self: object pointer
#         @return: raise a warning depending on the validation
#         """
#         ctx = dict(self._context) or {}
#         for reservation in self:
#             cap = 0
#             for rec in reservation.reservation_line:
#                 if len(rec.reserve) == 0:
#                     raise ValidationError(_("Please Select Billboards For Reservation."))
#                 cap = sum(room.capacity for room in rec.reserve)
#             if not ctx.get("duplicate"):
#                 if (reservation.adults + reservation.children) > cap:
#                     raise ValidationError(
#                         _(
#                             "Billboard Capacity Exceeded \n"
#                             " Please Select Billboards According to"
#                             " Members Accomodation."
#                         )
#                     )
#             if reservation.adults <= 0:
#                 raise ValidationError(_("Adults must be more than 0"))

    @api.constrains("checkin", "checkout")
    def check_in_out_dates(self):
        """
        When date_order is less then check-in date or
        Checkout date should be greater than the check-in date.
        """
        if self.checkout and self.checkin:
            if self.checkin < self.date_order:
                raise ValidationError(
                    _(
                        """Start date should be greater than """
                        """the current date."""
                    )
                )
            if self.checkout < self.checkin:
                raise ValidationError(
                    _("""End date should be greater """ """than Start date.""")
                )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel reservation as well
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        if not self.partner_id:
            self.update(
                {
                    "partner_invoice_id": False,
                    "partner_shipping_id": False,
                    "partner_order_id": False,
                }
            )
        else:
            addr = self.partner_id.address_get(["delivery", "invoice", "contact"])
            self.update(
                {
                    "partner_invoice_id": addr["invoice"],
                    "partner_shipping_id": addr["delivery"],
                    "partner_order_id": addr["contact"],
                    "pricelist_id": self.partner_id.property_product_pricelist.id,
                }
            )

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        vals["reservation_no"] = (
            self.env["ir.sequence"].next_by_code("hotel.reservation") or "New"
        )
        return super(HotelReservation, self).create(vals)

    def check_overlap(self, date1, date2):
        delta = date2 - date1
        return {date1 + timedelta(days=i) for i in range(delta.days + 1)}

    def confirmed_reservation(self):
        """
        This method create a new record set for hotel room reservation line
        -------------------------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel room reservation line.
        """
        reservation_line_obj = self.env["hotel.room.reservation.line"]
        vals = {}
        for reservation in self:
            reserv_checkin = reservation.checkin
            reserv_checkout = reservation.checkout 
            room_bool = False
            for line_id in reservation.reservation_line:
                for room in line_id.reserve:
                    if room.room_reservation_line_ids:
                        for reserv in room.room_reservation_line_ids.search(
                            [
                                ("status", "in", ("confirm", "done")),
                                ("room_id", "=", room.id),
                            ]
                        ):
                            check_in = reserv.check_in
                            check_out = reserv.check_out
                            if check_in <= reserv_checkin <= check_out:
                                room_bool = True
                            if check_in <= reserv_checkout <= check_out:
                                room_bool = True
                            if (
                                reserv_checkin <= check_in
                                and reserv_checkout >= check_out
                            ):
                                room_bool = True
                                
#                             if (
#                                 check_out == reserv_checkin  
#                                 or reserv_checkout == check_in
#                             ):
#                                 room_bool = True
                            
                            r_checkin = (reservation.checkin).date()
                            r_checkout = (reservation.checkout).date()
                            check_intm = (reserv.check_in).date()
                            check_outtm = (reserv.check_out).date()
                            range1 = [r_checkin, r_checkout]
                            range2 = [check_intm, check_outtm]
                            overlap_dates = self.check_overlap(
                                *range1
                            ) & self.check_overlap(*range2)
                            if room_bool:
                                raise ValidationError(
                                    _(
                                        "You tried to Confirm "
                                        "Reservation with Billboard"
                                        " those already "
                                        "reserved in this "
                                        "Reservation Period. "
                                        "Overlap Dates are "
                                        "%s"
                                    )
                                    % overlap_dates
                                )
                            else:
                                self.state = "confirm"
                                vals = {
                                    "room_id": room.id,
                                    "check_in": reservation.checkin,
                                    "check_out": reservation.checkout,
                                    "state": "assigned",
                                    "reservation_id": reservation.id,
                                }
                                room.write({"isroom": False, "status": "occupied"})
                        else:
                            self.state = "confirm"
                            vals = {
                                "room_id": room.id,
                                "check_in": reservation.checkin,
                                "check_out": reservation.checkout,
                                "state": "assigned",
                                "reservation_id": reservation.id,
                            }
                            room.write({"isroom": False, "status": "occupied"})
                    else:
                        self.state = "confirm"
                        vals = {
                            "room_id": room.id,
                            "check_in": reservation.checkin,
                            "check_out": reservation.checkout,
                            "state": "assigned",
                            "reservation_id": reservation.id,
                        }
                        room.write({"isroom": False, "status": "occupied"})
                    reservation_line_obj.create(vals)
        return True

    def cancel_reservation(self):
        """
        This method cancel record set for hotel room reservation line
        ------------------------------------------------------------------
        @param self: The object pointer
        @return: cancel record set for hotel room reservation line.
        """
        room_res_line_obj = self.env["hotel.room.reservation.line"]
        hotel_res_line_obj = self.env["hotel.reservation.line"]
        self.state = "cancel"
        room_reservation_line = room_res_line_obj.search(
            [("reservation_id", "in", self.ids)]
        )
        room_reservation_line.write({"state": "unassigned"})
        room_reservation_line.unlink()
        reservation_lines = hotel_res_line_obj.search([("line_id", "in", self.ids)])
        for reservation_line in reservation_lines:
            reservation_line.reserve.write({"isroom": True, "status": "available"})
        return True

    def set_to_draft_reservation(self):
        self.update({"state": "draft"})

    def action_send_reservation_mail(self):
        """
        This function opens a window to compose an email,
        template message loaded by default.
        @param self: object pointer
        """
        self.ensure_one(), "This is for a single id at a time."
        template_id = self.env.ref(
            "hotel_reservation.email_template_hotel_reservation"
        ).id
        compose_form_id = self.env.ref("mail.email_compose_message_wizard_form").id
        ctx = {
            "default_model": "hotel.reservation",
            "default_res_id": self.id,
            "default_use_template": bool(template_id),
            "default_template_id": template_id,
            "default_composition_mode": "comment",
            "force_send": True,
            "mark_so_as_sent": True,
        }
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form_id, "form")],
            "view_id": compose_form_id,
            "target": "new",
            "context": ctx,
            "force_send": True,
        }

    @api.model
    def reservation_reminder_24hrs(self):
        """
        This method is for scheduler
        every 1day scheduler will call this method to
        find all tomorrow's reservations.
        ----------------------------------------------
        @param self: The object pointer
        @return: send a mail
        """
        now_date = fields.Date.today()
        template_id = self.env.ref(
            "hotel_reservation.mail_template_reservation_reminder_24hrs"
        )
        for reserv_rec in self:
            checkin_date = reserv_rec.checkin
            difference = relativedelta(now_date, checkin_date)
            if (
                difference.days == -1
                and reserv_rec.partner_id.email
                and reserv_rec.state == "confirm"
            ):
                template_id.send_mail(reserv_rec.id, force_send=True)
        return True

    def create_folio(self):
        """
        This method is for create new hotel folio.
        -----------------------------------------
        @param self: The object pointer
        @return: new record set for hotel folio.
        """
        hotel_folio_obj = self.env["hotel.folio"]
        for reservation in self:
            folio_lines = []
            checkin_date = reservation["checkin"]
            checkout_date = reservation["checkout"]
            duration_vals = self._onchange_check_dates(
                checkin_date=checkin_date,
                checkout_date=checkout_date,
                duration=False,
            )
            duration = duration_vals.get("duration") or 0.0
            folio_vals = {
                "date_order": reservation.date_order,
                "company_id": reservation.company_id.id,
                "partner_id": reservation.partner_id.id,
                "pricelist_id": reservation.pricelist_id.id,
                "partner_invoice_id": reservation.partner_invoice_id.id,
                "partner_shipping_id": reservation.partner_shipping_id.id,
                "checkin_date": reservation.checkin,
                "checkout_date": reservation.checkout,
                "duration": duration,
                "reservation_id": reservation.id,
            }
            for line in reservation.reservation_line:
                for r in line.reserve:
                    folio_lines.append(
                        (
                            0,
                            0,
                            {
                                "checkin_date": checkin_date,
                                "checkout_date": checkout_date,
                                "product_id": r.product_id and r.product_id.id,
                                "name": reservation["reservation_no"],
                                "price_unit": r.list_price,
                                "product_uom_qty": duration,
                                "is_reserved": True,
                            },
                        )
                    )
                    r.write({"status": "occupied", "isroom": False})
            folio_vals.update({"room_line_ids": folio_lines})
            folio = hotel_folio_obj.create(folio_vals)
            for rm_line in folio.room_line_ids:
                rm_line._onchange_product_id()
            self.write({"folio_id": [(6, 0, folio.ids)], "state": "done"})
        return True

    def _onchange_check_dates(
        self, checkin_date=False, checkout_date=False, duration=False
    ):
        """
        This method gives the duration between check in checkout if
        customer will leave only for some hour it would be considers
        as a whole day. If customer will checkin checkout for more or equal
        hours, which configured in company as additional hours than it would
        be consider as full days
        --------------------------------------------------------------------
        @param self: object pointer
        @return: Duration and checkout_date
        """
        value = {}
        configured_addition_hours = self.company_id.additional_hours
        duration = 0
        if checkin_date and checkout_date:
            dur = checkout_date - checkin_date
            duration = dur.days + 1
            if configured_addition_hours > 0:
                additional_hours = abs(dur.seconds / 60)
                if additional_hours <= abs(configured_addition_hours * 60):
                    duration -= 1
        value.update({"duration": duration})
        return value

    def open_folio_view(self):
        folios = self.mapped("folio_id")
        action = self.env.ref("hotel.open_hotel_folio1_form_tree_all").read()[0]
        if len(folios) > 1:
            action["domain"] = [("id", "in", folios.ids)]
        elif len(folios) == 1:
            action["views"] = [(self.env.ref("hotel.view_hotel_folio_form").id, "form")]
            action["res_id"] = folios.id
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action


class HotelReservationLine(models.Model):

    _name = "hotel.reservation.line"
    _description = "Reservation Line"
    
    name = fields.Char("Name")
    line_id = fields.Many2one("hotel.reservation")
    reserve = fields.Many2many(
        "hotel.room",
        "hotel_reservation_line_room_rel",
        "hotel_reservation_line_id",
        "room_id",
        domain="[('isroom','=',True),\
                               ('categ_id','=',categ_id)]",
    )
    categ_id = fields.Many2one("hotel.room.type", "Room Type")
    
    checkin = fields.Datetime(
        "Start Date",
        required=True,
        readonly=True,
        related = "line_id.checkin",
    )
    checkout = fields.Datetime(
        "End Date",
        required=True,
        readonly=True,
        related = "line_id.checkout",
        
    )
     

    @api.onchange("categ_id","checkin","checkout")
    def on_change_categ(self):
        """
        When you change categ_id it check checkin and checkout are
        filled or not if not then raise warning
        -----------------------------------------------------------
        @param self: object pointer
        """
        if not self.line_id.checkin:
            raise ValidationError(
                _(
                    """Before choosing a Billboard,\n You have to """
                    """select a Start date and an End Date """
                    """in the reservation form."""
                )
            )
        hotel_room_ids = self.env["hotel.room"].search(
            [("room_categ_id", "=", self.categ_id.id)]
        )
        room_ids = []
        for room in hotel_room_ids:
            assigned = False
            for line in room.room_reservation_line_ids.filtered(
                lambda l: l.status != "cancel"
            ):
                if self.line_id.checkin and line.check_in and self.line_id.checkout:
                    if (
                        self.line_id.checkin <= line.check_in <= self.line_id.checkout 
#                         - relativedelta(days=3)
                    ) or (
                        self.line_id.checkin <= line.check_out <= self.line_id.checkout 
                    ):
                        assigned = True
                    elif (
                        self.line_id.checkin <= line.check_in <= self.line_id.checkout 
                    ) or (
                        self.line_id.checkin <= line.check_out <= self.line_id.checkout
                    ):
                        assigned = True
                    elif (line.check_in <= self.line_id.checkin <= line.check_out) or (
                        line.check_in <= self.line_id.checkout <= line.check_out
                    ):
                        assigned = True
                        
                    if (
                        line.check_in <= self.line_id.checkout < line.check_in + relativedelta(days=1)
                    ) or (
                        line.check_out <= self.line_id.checkin < line.check_out + relativedelta(days=1)
                    ):
                        assigned = True
                        
            for rm_line in room.room_line_ids.filtered(lambda l: l.status != "cancel"):
                if self.line_id.checkin and rm_line.check_in and self.line_id.checkout:
                    if (
                        self.line_id.checkin
                        <= rm_line.check_in
                        <= self.line_id.checkout
                    ) or (
                        self.line_id.checkin
                        <= rm_line.check_out
                        <= self.line_id.checkout
                    ):
                        assigned = True
                    elif (
                        rm_line.check_in <= self.line_id.checkin <= rm_line.check_out
                    ) or (
                        rm_line.check_in <= self.line_id.checkout <= rm_line.check_out
                    ):
                        assigned = True
                        
                    if (
                        rm_line.check_in <= self.line_id.checkout < rm_line.check_in + relativedelta(days=1)
                    ) or (
                        rm_line.check_out <= self.line_id.checkin < rm_line.check_out + relativedelta(days=1)
                    ):
                        assigned = True 
                        
            if not assigned:
                room_ids.append(room.id)
        domain = {"reserve": [("id", "in", room_ids)]}
        return {"domain": domain}

    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        hotel_room_reserv_line_obj = self.env["hotel.room.reservation.line"]
        for reserv_rec in self:
            for rec in reserv_rec.reserve:
                myobj = hotel_room_reserv_line_obj.search(
                    [
                        ("room_id", "=", rec.id),
                        ("reservation_id", "=", reserv_rec.line_id.id),
                    ]
                )
                if myobj:
                    rec.write({"isroom": True, "status": "available"})
                    myobj.unlink()
        return super(HotelReservationLine, self).unlink()


class HotelRoomReservationLine(models.Model):

    _name = "hotel.room.reservation.line"
    _description = "Hotel Room Reservation"
    _rec_name = "room_id"

    room_id = fields.Many2one("hotel.room", string="Billboard id")
    check_in = fields.Datetime("Start Date", required=True)
    check_out = fields.Datetime("End Date", required=True)
    state = fields.Selection(
        [("assigned", "Assigned"), ("unassigned", "Unassigned")], "Billboard Status"
    )
    reservation_id = fields.Many2one("hotel.reservation", "Reservation")
    status = fields.Selection(string="state", related="reservation_id.state")
