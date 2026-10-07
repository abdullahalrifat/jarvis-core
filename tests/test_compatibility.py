from jarvis_core.compatibility import ComponentVersion, report

def test_exact_core_contract_is_compatible():
    result = report("0.16.1", "0.16.1", ComponentVersion("jarvis", "0.10.4"))
    assert result.compatible is True
    assert "exact" in result.reason

def test_drift_is_not_silently_accepted():
    result = report("0.16.2", "0.16.1")
    assert result.compatible is False
