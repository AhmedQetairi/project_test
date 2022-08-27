# See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class QuickRoomReservation(models.TransientModel):
    _name = "quick.room.reservation"
    _description = "Quick Room Reservation"
    
    
    
    reservation_id = fields.Many2one("hotel.reservation", "Reservation")
    reservation_no = fields.Char("Reservation No" , related="reservation_id.reservation_no")
    
    date_order = fields.Datetime(
        "Date Ordered",
        readonly=True,
        required=True,
        index=True,
        default=lambda self: fields.Datetime.now(),
    )
    
    room_id = fields.Many2one("hotel.room", "Room", required=True)

    checkin = fields.Datetime(
        "Start Date",
        required=True,
        
        states={"draft": [("readonly", False)]},
    )
    checkout = fields.Datetime(
        "End Date",
        required=True,
        
        states={"draft": [("readonly", False)]},
    )
    
    
#     date_from_test = fields.Datetime("Date From", default=lambda self: fields.Date.today())
#     date_to_test = fields.Datetime("Date To", default=lambda self: fields.Date.today() + relativedelta(days=30),)
    
   
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
#     folio_id = fields.Many2many(
#         "hotel.folio",
#         "hotel_folio_reservation_rel",
#         "order_id",
#         "invoice_id",
#         string="Folio",
#     )
    
#     no_of_folio = fields.Integer("No. Folio", compute="_compute_folio_count")
    
#     summary_header = fields.Text("Summary Header")
#     room_summary = fields.Text("Room Summary")
    
#     goal_rooms_test = fields.Many2many("hotel.room")

#     partner_id = fields.Many2one("res.partner", "Customer", required=True)
#     check_in = fields.Datetime("Check In", required=True)
#     check_out = fields.Datetime("Check Out", required=True)
#     room_id = fields.Many2one("hotel.room", "Room", required=True)
#     company_id = fields.Many2one("res.company", "Hotel", required=True)
#     pricelist_id = fields.Many2one("product.pricelist", "pricelist")
#     partner_invoice_id = fields.Many2one(
#         "res.partner", "Invoice Address", required=True
#     )
#     partner_order_id = fields.Many2one("res.partner", "Ordering Contact", required=True)
#     partner_shipping_id = fields.Many2one(
#         "res.partner", "Delivery Address", required=True
#     )
#     adults = fields.Integer("Adults")

#     @api.onchange("check_out", "check_in")
#     def _on_change_check_out(self):
#         """
#         When you change checkout or checkin it will check whether
#         Checkout date should be greater than Checkin date
#         and update dummy field
#         -----------------------------------------------------------
#         @param self: object pointer
#         @return: raise warning depending on the validation
#         """
#         if (self.check_out and self.check_in) and (self.check_out < self.check_in):
#             raise ValidationError(
#                 _("Checkout date should be greater than Checkin date.")
#             )

    
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
#         return super(QuickRoomReservation, self).unlink()
    
    
    @api.onchange("partner_id")
    def _onchange_partner_id_res(self):
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
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        res = super(QuickRoomReservation, self).default_get(fields)
        keys = self._context.keys()
         
        if "date" in keys:
            res.update({"checkin": self._context["date"]})      
            
        if "room_id" in keys:
            roomid = self._context["room_id"]
            res.update({"room_id": int(roomid)})
            
        return res
    
    
    def cancel_reservation(self):
        """
        This method cancel record set for hotel room reservation line
        ------------------------------------------------------------------
        @param self: The object pointer
        @return: cancel record set for hotel room reservation line.
        """
        room_res_line_obj = self.env["hotel.room.reservation.line"]
        hotel_res_line_obj = self.env["hotel.reservation.line"]
        
        hotel_res_line_obj_reservation = self.env["hotel.reservation"]
        hotel_res_line_obj_reservation.state = "cancel"
        
        room_reservation_line = room_res_line_obj.search(
            [("reservation_id", "=", self.reservation_id.id),('room_id', '=', self.room_id.id)]
        )
        
        room_reservation_line.write({"check_in": self.checkin,
                                     "check_out": self.checkout,
                                    })
#         room_reservation_line.unlink()
        
        reservation_lines = hotel_res_line_obj.search([("line_id", "in", self.ids)])
        for reservation_line in reservation_lines:
            reservation_line.reserve.write({"isroom": True, "status": "available"})
        return True
    

    def room_reserve(self):
        """
        This method create a new record for hotel.reservation
        -----------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel reservation.
        """
        hotel_res_obj = self.env["hotel.reservation"]
        for res in self:
            rec = hotel_res_obj.create(
                {
                    
                    "checkin": res.checkin,
                    "checkout": res.checkout,
                    
                
                    "reservation_line": [
                        (
                            0,
                            0,
                            {
                                "reserve": [(6, 0, res.room_id.ids)],
                                "name": res.room_id.name or " ",
                            },
                        )
                    ],
                }
            )
        return rec
