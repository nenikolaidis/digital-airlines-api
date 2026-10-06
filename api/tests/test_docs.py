from openapi_spec_validator import validate

from airline.openapi import SPEC, openapi_path

# Routes that serve the docs themselves, rather than the API
UNDOCUMENTED = {"/", "/docs", "/openapi.json"}


def test_spec_is_valid_openapi():
    validate(SPEC)


def test_spec_matches_the_routes(app):
    routes = set()
    for rule in app.url_map.iter_rules():
        path = openapi_path(rule.rule)
        if rule.endpoint == "static" or path in UNDOCUMENTED:
            continue
        routes |= {(path, method.lower()) for method in rule.methods - {"HEAD", "OPTIONS"}}

    documented = {(path, method) for path, item in SPEC["paths"].items() for method in item if method != "parameters"}
    assert documented == routes


def test_docs_are_served(anon):
    assert anon.get("/openapi.json").get_json()["info"]["title"] == "Digital Airlines API"
    page = anon.get("/docs")
    assert page.status_code == 200
    assert "swagger-ui" in page.get_data(as_text=True)
