# # content of conftest.py
# import pytest

# def pytest_addoption(parser):
#     parser.addoption("--frameworks", action="store_true", help="Run only framework specific tests.")

# def pytest_configure(config):
#     # Register an additional marker
#     config.addinivalue_line("markers",
#         "framework(name): mark test as an intergration test for a framework (e.g. flask, django)")

# def pytest_runtest_setup(item):
#     marked = list(item.iter_markers(name='framework'))
#     if marked:
#         import pdb; pdb.set_trace()
#         if item.config.getoption("--frameworks"):
#             pytest.skip("test is for a framework")