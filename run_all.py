"""run_all.py — runs the full scanner pipeline and opens the dashboard."""
import subprocess, sys, os, webbrowser, time, json
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = r"D:\MOVED FROM C\Python\venvs\py311\Scripts\python.exe"

def run(name, cmd, cwd=None, tolerant=False):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    t0 = time.time()
    # Always show stdout live; suppress yfinance's noisy stderr
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd or SCRIPT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if result.stdout:
        print(result.stdout)
    elapsed = time.time() - t0
    if result.returncode != 0 and not tolerant:
        print(f"[FAIL] {name} exited with code {result.returncode}")
        sys.exit(1)
    print(f"[OK]   {name} done in {elapsed:.1f}s")
    return elapsed

def main():
    total = time.time()
    print(f"Nifty 213 Scanner Pipeline — {datetime.now():%Y-%m-%d %H:%M:%S}")

    # Step 1: Scan (tolerant — delisted stocks cause yfinance 404s but results file is still written)
    run("Step 1: Scanner v2", [PYTHON, "scanner_v2.py"], tolerant=True)

    # Step 2: Score
    run("Step 2: Scorer",    [PYTHON, "scorer.py"])

    # Step 3: Report
    run("Step 3: Report",    [PYTHON, "report.py"])

    # Open dashboard
    dash = os.path.join(SCRIPT_DIR, "dashboard.html")
    if os.path.exists(dash):
        print(f"\nOpening dashboard...")
        webbrowser.open(f"file://{dash}")
    else:
        print(f"[WARN] dashboard.html not found at {dash}")

    # Summary
    print(f"\nTotal pipeline time: {time.time()-total:.1f}s")
    print("Pipeline complete. Check scanner_results.json and scored_results.json for raw data.")

if __name__ == "__main__":
    main()
