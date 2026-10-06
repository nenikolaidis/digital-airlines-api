import math

from flask import request

from .errors import APIError

DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def query_int(name, default, maximum=None):
    value = request.args.get(name)
    if value is None or value == "":
        return default
    if not value.isdigit() or int(value) < 1:
        raise APIError(400, f"{name} must be a whole number of 1 or more.")
    if maximum and int(value) > maximum:
        raise APIError(400, f"{name} can be at most {maximum}.")
    return int(value)


def paginate(collection, query, sort, view, **find_options):
    """One page of the matching documents, plus page metadata, from ?page= and ?per_page=."""
    page = query_int("page", 1)
    per_page = query_int("per_page", DEFAULT_PER_PAGE, MAX_PER_PAGE)

    total = collection.count_documents(query, **find_options)
    cursor = collection.find(query, **find_options).sort(sort).skip((page - 1) * per_page).limit(per_page)
    items = [view(document) for document in cursor]
    meta = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": math.ceil(total / per_page),
        "count": len(items),
    }
    return meta, items
