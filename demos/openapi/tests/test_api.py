import threading
import time
import requests
import json
import yaml
import importlib.util
import pathlib
from jsonschema import validate


def load_app_module():
    # load demos/openapi/app.py as a module when running tests from repo root
    repo_root = pathlib.Path(__file__).resolve().parents[3]
    app_path = repo_root / 'demos' / 'openapi' / 'app.py'
    spec = importlib.util.spec_from_file_location('demo_app', str(app_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def start_server():
    demo_mod = load_app_module()
    demo_mod.run(port=8080)


def load_spec():
    with open('demos/openapi/spec.yaml') as f:
        return yaml.safe_load(f)


def test_list_and_create():
    t = threading.Thread(target=start_server, daemon=True)
    t.start()

    # wait for server to start with retries
    for _ in range(10):
        try:
            r = requests.get('http://127.0.0.1:8080/todos', timeout=1)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    else:
        raise RuntimeError('Server did not start in time')

    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)

    r2 = requests.post('http://127.0.0.1:8080/todos', json={'title': 'write tests'})
    assert r2.status_code == 201
    created = r2.json()
    assert created['title'] == 'write tests'

    spec = load_spec()
    todo_schema = spec['components']['schemas']['Todo']
    # validate created object against schema
    validate(instance=created, schema=todo_schema)
