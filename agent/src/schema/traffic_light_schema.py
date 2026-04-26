from marshmallow import Schema, fields
from schema.gps_schema import GpsSchema

class TrafficLightSchema(Schema):
    user_id = fields.Int()
    light_id = fields.Str()
    current_state = fields.Str()
    car_count = fields.Int()
    gps = fields.Nested(GpsSchema)
    timestamp = fields.DateTime("iso")
