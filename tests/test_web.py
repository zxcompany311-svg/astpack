from astpack.web import HTML_TEMPLATE


def test_web_template():
    assert "AstPack Playground" in HTML_TEMPLATE
    assert "/api/prune" in HTML_TEMPLATE
    assert "highlight.js" in HTML_TEMPLATE
    assert "depth-select" in HTML_TEMPLATE
    assert "signatures" in HTML_TEMPLATE
