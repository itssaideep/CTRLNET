import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = "ctrlnet/database/ctrlnet.db"

def view_results():
    if not Path(DB_PATH).exists():
        print(f"Database not found at {DB_PATH}. Has a scan run yet?")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n" + "="*60)
    print(" [CTRLNET] AUTONOMOUS SCAN RESULTS")
    print("="*60 + "\n")

    # Get recent evidence and targets
    cursor.execute("""
        SELECT e.target_id, e.service, e.port, p.cpe, p.cves, p.abstained, p.confidence, ec.timestamp
        FROM evidence e
        JOIN experiment_configs ec ON e.run_id = ec.run_id
        LEFT JOIN predictions p ON p.evidence_id = e.id
        ORDER BY ec.timestamp DESC
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("No scan results found in database yet. Waiting for Scout to discover targets...")
        return
        
    for r in rows:
        print(f"[{r['timestamp']}] Target: {r['target_id']}:{r['port']} ({r['service']})")
        if r['abstained']:
            print(f"  -> LLM Abstained (Confidence: {r['confidence']}) - Insufficient Evidence")
        else:
            print(f"  -> Predicted CPE: {r['cpe']}")
            if r['cves']:
                try:
                    cve_list = json.loads(r['cves'])
                    print(f"  -> Vulnerabilities ({len(cve_list)}): {', '.join(cve_list[:3])}{'...' if len(cve_list) > 3 else ''}")
                except:
                    print(f"  -> Vulnerabilities: {r['cves']}")
        print("-" * 40)

if __name__ == "__main__":
    view_results()
