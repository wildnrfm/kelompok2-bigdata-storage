import datetime
import json


def _hook(d):
    if len(d) == 1 and "$date" in d:
        return datetime.datetime.strptime(d["$date"], "%Y-%m-%dT%H:%M:%S.%fZ")
    return d


def loads(teks):
    return json.loads(teks, object_hook=_hook)
