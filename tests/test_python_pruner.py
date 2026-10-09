import ast
import os
from pathlib import Path
from astpack.pruner import prune_file, prune_code
from astpack.analyzer.python import PythonAnalyzer


def test_python_analyzer_parse():
    sample_file = Path(__file__).parent / "sample_code" / "ecommerce_app.py"
    with open(sample_file, "r", encoding="utf-8") as f:
        code = f.read()

    analyzer = PythonAnalyzer()
    analysis = analyzer.parse(code, str(sample_file))

    assert analysis.language == "python"
    assert len(analysis.symbols) >= 4
    assert any(s.name == "process_order" for s in analysis.symbols)
    assert any(s.name == "PaymentGateway" for s in analysis.symbols)


def test_prune_all_stubs():
    sample_file = Path(__file__).parent / "sample_code" / "ecommerce_app.py"
    pruned, stats = prune_file(str(sample_file), mode="stubs")

    # Pruned code must be syntactically valid Python
    tree = ast.parse(pruned)
    assert tree is not None

    # Ellipsis must be present in stubbed bodies
    assert "..." in pruned
    # Docstrings should be retained in stubs mode
    assert "Calculate shipping cost based on weight" in pruned
    assert stats["reduction_pct"] > 30.0


def test_prune_signatures_mode():
    sample_file = Path(__file__).parent / "sample_code" / "ecommerce_app.py"
    pruned, stats = prune_file(str(sample_file), mode="signatures")

    tree = ast.parse(pruned)
    assert tree is not None

    # Signatures mode MUST strip docstrings
    assert "Calculate shipping cost based on weight" not in pruned
    assert "Charge credit card via external API" not in pruned
    assert "def calculate_shipping" in pruned
    assert "..." in pruned
    # Signatures mode should save more tokens than stubs mode
    assert stats["reduction_pct"] > 40.0


def test_prune_focus_mode_with_closure():
    sample_file = Path(__file__).parent / "sample_code" / "ecommerce_app.py"
    pruned, stats = prune_file(str(sample_file), focus=["process_order"], mode="focus", depth=1)

    # Syntactically valid
    tree = ast.parse(pruned)
    assert tree is not None

    # Focused primary target function body should be preserved intact
    assert "grand_total = total + shipping" in pruned
    assert "ORD-99881" in pruned

    # Immediate dependency (calculate_shipping) should have body stubbed but docstring preserved
    assert "base_rate = 5.0" not in pruned
    assert "Calculate shipping cost based on weight" in pruned

    # Unrelated function (PaymentGateway.refund) should have docstring stripped in focus mode
    assert "Issue refund to customer" not in pruned
    assert stats["saved_tokens"] > 0
