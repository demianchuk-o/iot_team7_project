from marshmallow import Schema, fields
from schema.gps_schema import GpsSchema

class ParkingSchema(Schema):
    user_id = fields.Int()
    parking_id = fields.Str()
    is_occupied = fields.Bool()
    total_spots = fields.Int()
    gps = fields.Nested(GpsSchema)
    timestamp = fields.DateTime("iso")
