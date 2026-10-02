from policy_diff.tracker import compare_snapshots, normalize_html


def test_normalize_html_removes_scripts_and_collapses_space():
    assert normalize_html("<script>bad()</script><p>Terms   of\n service</p>") == "Terms of service"


def test_diff_reports_changed_text():
    unified, page = compare_snapshots("A\nold clause", "A\nnew clause")
    assert "-old clause" in unified and "+new clause" in unified
    assert "new clause" in page
