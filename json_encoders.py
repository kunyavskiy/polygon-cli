from polygon_file import PolygonFile


def my_json_encoder(obj):
    if isinstance(obj, PolygonFile):
        res = obj.__dict__
        res.update({'__type': 'PolygonFile'})
        return res
    raise TypeError("Unknown type in my_json_encoder")


def my_json_decoder(dct):
    if '__type' not in dct:
        return dct
    if dct['__type'] == 'PolygonFile':
        res = PolygonFile()
        res.by_dict(dct)
        return res
    raise TypeError("Unknown type in my_json_decoder")
