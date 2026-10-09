import ast
from astpack.pruner import prune_code
from astpack.graph.resolver import DependencyGraph
from astpack.analyzer.python import PythonAnalyzer


def test_depth_zero_vs_one():
    code = """
def step_three() -> int:
    return 3

def step_two() -> int:
    return step_three()

def step_one() -> int:
    '''Starting execution.'''
    return step_two()
"""
    # depth=0: Only step_one is primary, no dependencies tracked
    pruned_d0, stats_d0 = prune_code(code, filepath="pipeline.py", focus=["step_one"], mode="focus", depth=0)
    assert "return step_two()" in pruned_d0
    # step_two should be stripped of docstrings / treated as unrelated in depth 0
    assert "def step_two() -> int:\n    ..." in pruned_d0
    assert len(stats_d0["dependency_targets"]) == 0

    # depth=1: step_two is tracked as dependency
    pruned_d1, stats_d1 = prune_code(code, filepath="pipeline.py", focus=["step_one"], mode="focus", depth=1)
    assert "step_two" in stats_d1["dependency_targets"]
    assert "step_three" not in stats_d1["dependency_targets"]

    # depth=2: step_three is also tracked
    pruned_d2, stats_d2 = prune_code(code, filepath="pipeline.py", focus=["step_one"], mode="focus", depth=2)
    assert "step_two" in stats_d2["dependency_targets"]
    assert "step_three" in stats_d2["dependency_targets"]


def test_import_aware_resolution():
    analyzer = PythonAnalyzer()

    code_payment = """
def charge(amount: float) -> bool:
    '''Process payment.'''
    return True
"""
    analysis_payment = analyzer.parse(code_payment, "payment.py")

    code_app = """
from payment import charge as do_charge

def checkout(val: float) -> bool:
    '''User checkout flow.'''
    return do_charge(val)
"""
    analysis_app = analyzer.parse(code_app, "app.py")

    graph = DependencyGraph()
    graph.add_file(analysis_payment)
    graph.add_file(analysis_app)

    layers = graph.resolve_layers({"checkout"}, max_depth=1)
    assert "checkout" in layers["primary"]
    # Should resolve do_charge -> charge in payment.py
    assert "charge" in layers["dependencies"]
