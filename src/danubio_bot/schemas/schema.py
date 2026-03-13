import re

from marshmallow import Schema, ValidationError, fields, validates

MSISDN_RE = re.compile(r"^\+?[0-9]{10,14}$")


class StartConversationSchema(Schema):
    msisdn = fields.String(required=True)
    template_id = fields.String(required=True)
    template_tokens = fields.List(fields.String(), required=True)
    location_id = fields.String(required=False)
    team_id = fields.String(required=False)
    type = fields.String(required=False)
    attachment_url = fields.String(required=False)
    options = fields.List(fields.String(), required=False)

    @validates("msisdn")
    def validate_msisdn(self, msisdn):
        if not MSISDN_RE.match(msisdn):
            print("3: {}".format(msisdn))
            raise ValidationError("Malformed MSISDN")


class VoucherSchema(Schema):
    code = fields.String(required=True)
    fulfillment = fields.String(required=True)


class FulfillmentItemSchema(Schema):
    sku = fields.String(required=True)
    quantity = fields.Number(required=True)
    name = fields.String(required=False)


class FulfillmentSchema(Schema):
    status = fields.String(required=True)
    type = fields.String(required=True)
    id = fields.String(required=True)
    items = fields.List(fields.Nested(FulfillmentItemSchema), required=False)


class OrderIdSchema(Schema):
    msisdn = fields.String(required=True)
    order_id = fields.String(required=False)
    pre_order_id = fields.String(required=False)
    channel = fields.String(required=False)
    order_status = fields.String(required=False)
    vouchers = fields.List(fields.Nested(VoucherSchema), required=False)
    fulfillments = fields.List(
        fields.Nested(FulfillmentSchema), required=False
    )

    @validates("msisdn")
    def validate_msisdn(self, msisdn):
        if not MSISDN_RE.match(msisdn):
            print("4: {}".format(msisdn))
            raise ValidationError("Malformed MSISDN")


class SendMessageSchema(Schema):
    msisdn = fields.String(required=True)
    message = fields.String(required=True)

    @validates("msisdn")
    def validate_msisdn(self, msisdn):
        if not MSISDN_RE.match(msisdn):
            print("5: {}".format(msisdn))
            raise ValidationError("Malformed MSISDN")


class SendProductImageSchema(Schema):
    msisdn = fields.String(required=True)
    sku = fields.String(required=True)

    @validates("msisdn")
    def validate_msisdn(self, msisdn):
        if not MSISDN_RE.match(msisdn):
            print("6: {}".format(msisdn))
            raise ValidationError("Malformed MSISDN")


class SummaryItemSchema(Schema):
    name = fields.String(required=True)
    quantity = fields.Integer(required=True)


class SendSummarySchema(Schema):
    msisdn = fields.String(required=True)
    freight_cost = fields.Decimal(required=True)
    total = fields.Decimal(required=True)
    sub_total = fields.Decimal(required=True)
    items = fields.List(fields.Nested(SummaryItemSchema))
    link = fields.String(required=True)


class SendMessageIdSchema(Schema):
    msisdn = fields.String(required=True)
    message_id = fields.String(required=True)
    params = fields.Dict(required=True)

    @validates("msisdn")
    def validate_msisdn(self, msisdn):
        if not MSISDN_RE.match(msisdn):
            print("7: {}".format(msisdn))
            raise ValidationError("Malformed MSISDN")
