import importlib.util
import pathlib

import yaml
from jsonschema import validate


def load_app_module():
    repo_root = pathlib.Path(__file__).resolve().parents[3]
    app_path = repo_root / "demos" / "openapi" / "app.py"
    spec = importlib.util.spec_from_file_location("demo_app", str(app_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_spec():
    repo_root = pathlib.Path(__file__).resolve().parents[3]
    spec_path = repo_root / "demos" / "openapi" / "spec.yaml"
    with open(spec_path) as f:
        return yaml.safe_load(f)


def test_list_todos_and_create_todo():
    module = load_app_module()
    client = module.app.test_client()

    response = client.get("/todos")
    assert response.status_code == 200
    todos = response.get_json()
    assert isinstance(todos, list)

    create_response = client.post("/todos", json={"title": "write tests"})
    assert create_response.status_code == 201
    created = create_response.get_json()
    assert created["title"] == "write tests"
    assert created["done"] is False

    spec = load_spec()
    todo_schema = spec["components"]["schemas"]["Todo"]
    validate(instance=created, schema=todo_schema)

    response_after = client.get("/todos")
    assert len(response_after.get_json()) >= 2


def test_create_without_title_returns_bad_request():
    module = load_app_module()
    client = module.app.test_client()

    response = client.post("/todos", json={})
    assert response.status_code == 400
    assert response.get_json() == {"error": "title required"}


def test_readiness_default_ok():
    module = load_app_module()
    client = module.app.test_client()

    response = client.get("/ready")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_readiness_fails_when_env_set(monkeypatch):
    monkeypatch.setenv("FAIL_READY", "true")
    module = load_app_module()
    client = module.app.test_client()

    response = client.get("/ready")
    assert response.status_code == 500
    assert response.get_json() == {"status": "not ready"}
