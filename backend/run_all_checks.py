import subprocess
import sys

SCRIPTS = [
    ("Analyzer Heuristics", "backend/test_backend.py"),
    ("HTTP API & Endpoints", "backend/test_api.py"),
    ("SSRF & Provider Integrations", "backend/test_providers.py"),
    ("Bilingual Field Coverage", "backend/test_bilingual.py"),
    ("Edge Cases & Unicode Polish", "backend/test_edge_cases.py"),
    ("Fact-Check Relevance & Verification", "backend/test_fact_check.py"),
    ("URL Security & Input Validation", "backend/test_url_security.py"),
    ("FastAPI HTTP E2E & Middleware", "backend/test_http_e2e.py"),
]

def run_suite():
    print("=" * 65)
    print("TrustShield AI — Comprehensive Verification Test Suite")
    print("=" * 65)

    all_passed = True
    python_bin = sys.executable or "python3"
    for name, script_path in SCRIPTS:
        print(f"\n[RUNNING] {name} ({script_path})...")
        res = subprocess.run(
            [python_bin, script_path],
            env={"PYTHONPATH": "backend"},
            capture_output=True,
            text=True
        )
        if res.returncode == 0:
            print(f"[PASS] {name}")
            for line in res.stdout.strip().split("\n"):
                print(f"       {line}")
        else:
            print(f"[FAIL] {name}")
            print(res.stderr or res.stdout)
            all_passed = False

    print("\n" + "=" * 65)
    if all_passed:
        print(f"RESULT: ALL {len(SCRIPTS)} VERIFICATION SUITES PASSED SUCCESSFULLY (0 FAILURES)")
    else:
        print("RESULT: ONE OR MORE VERIFICATION SUITES FAILED")
    print("=" * 65)
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run_suite())
