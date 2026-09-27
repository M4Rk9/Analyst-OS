from importlib import import_module


def test_core_packages_import() -> None:
    for module_name in (
        "analyst_os_analytics",
        "analyst_os_ingestion",
        "analyst_os_ai",
    ):
        module = import_module(module_name)
        assert module is not None
