from marshmallow import INCLUDE, Schema, fields


class SendTextMessageSchema(Schema):
    chat_id = fields.String(required=True, data_key="chat_id")
    message = fields.String(required=True, data_key="message")


class SendButtonMessageSchema(Schema):
    chat_id = fields.String(required=True, data_key="chat_id")
    body = fields.String(required=True, data_key="body")
    buttons = fields.List(fields.String(), required=True, data_key="buttons")

    class Meta:
        unknown = INCLUDE


class SendTemplateMessageSchema(Schema):
    template_id = fields.String(required=True, data_key="template_id")
    msisdn = fields.String(required=True, data_key="msisdn")
    template_tokens = fields.List(
        fields.String(), default=[], required=False, data_key="template_tokens"
    )

    class Meta:
        unknown = INCLUDE


class ImageAttachmentSchema(Schema):
    name = fields.String(required=True, data_key="name")
    file = fields.String(required=True, data_key="file")


class SendImageMessageSchema(Schema):
    chat_id = fields.String(required=True, data_key="chat_id")
    attachment = fields.Nested(
        ImageAttachmentSchema(), required=True, data_key="attachment"
    )
