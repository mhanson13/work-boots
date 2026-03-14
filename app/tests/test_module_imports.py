import importlib


def test_deps_module_imports() -> None:
    module = importlib.import_module("app.api.deps")
    assert module is not None
