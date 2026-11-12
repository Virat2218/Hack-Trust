from app.analyzers.url_analyzer import check_ssrf_strict
from app.providers.safe_browsing import SafeBrowsingProvider
from app.providers.fact_check import FactCheckProvider

def test_ssrf_strict_guard():
    # 1. Loopbacks & local addresses
    blocked_cases = [
        "127.0.0.1",
        "localhost",
        "127.0.1.1",
        "0.0.0.0",
        "::1",
        "169.254.169.254", # Cloud metadata
        "10.0.0.1",        # Private RFC1918 Class A
        "192.168.1.100",   # Private RFC1918 Class C
        "172.16.5.1",      # Private RFC1918 Class B
        "metadata.google.internal",
        "test.local",
        "test.internal",
        "2130706433",      # Decimal for 127.0.0.1
    ]

    for host in blocked_cases:
        is_safe, msg = check_ssrf_strict(host)
        assert not is_safe, f"Expected {host} to be BLOCKED, but check_ssrf_strict returned safe."
    print(f"✓ All {len(blocked_cases)} SSRF malicious/internal destinations successfully blocked.")

    # 2. Public domains
    is_safe, _ = check_ssrf_strict("example.com")
    assert is_safe, "Expected example.com to be permitted."
    print("✓ Public domain check passed.")

def test_safe_browsing_unconfigured_honest_state():
    provider = SafeBrowsingProvider(api_key="")
    assert not provider.is_configured()
    res = provider.check("https://example.com")
    assert res.provider_status.status == "NOT_CONFIGURED"
    assert not res.provider_status.configured
    assert len(res.signals) == 0
    print("✓ Safe Browsing honest unconfigured state verified.")

def test_fact_check_unconfigured_honest_state():
    provider = FactCheckProvider(api_key="")
    assert not provider.is_configured()
    res = provider.check("Some random claim")
    assert res.provider_status.status == "NOT_CONFIGURED"
    assert not res.provider_status.configured
    assert len(res.signals) == 0
    print("✓ Fact Check honest unconfigured state verified.")

if __name__ == "__main__":
    test_ssrf_strict_guard()
    test_safe_browsing_unconfigured_honest_state()
    test_fact_check_unconfigured_honest_state()
    print("All Phase 6 Safe URL & Provider tests passed successfully!")

