from solution import solution


def my_json_encoder(obj):
    if isinstance(obj, solution):
        res = obj.__dict__
        res.update({'__type': 'Solution'})
        return res
    raise TypeError("Unknown type in my_json_encoder")


def my_json_decoder(dct):
    if '__type' not in dct:
        return dct
    if dct['__type'] == 'Solution':
        res = solution()
        res.byDict(dct)
        return res
    raise TypeError("Unknown type in my_json_decoder")
