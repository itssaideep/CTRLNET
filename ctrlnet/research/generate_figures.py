import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from ctrlnet.config import config

def get_latest_run_id(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT run_id FROM experiment_configs ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    return row[0] if row else None

def generate_all_figures():
    print(f"Generating figures from {config.database_path}...")
    if not os.path.exists(config.database_path):
        print("Database not found.")
        return

    conn = sqlite3.connect(config.database_path)
    run_id = get_latest_run_id(conn)
    if not run_id:
        print("No experiment runs found.")
        return

    print(f"Using run_id: {run_id}")
    
    # We want to join evidence and evaluations
    query = """
    SELECT 
        e.evidence_level,
        ev.verdict,
        ev.failure_category,
        ev.product_accurate,
        ev.version_accurate,
        ev.cpe_accurate,
        ev.cve_precision,
        ev.cve_recall,
        p.confidence,
        p.abstained
    FROM evidence e
    JOIN predictions p ON p.evidence_id = e.id
    JOIN evaluations ev ON ev.prediction_id = p.id
    WHERE e.run_id = ?
    """
    
    df = pd.read_sql_query(query, conn, params=(run_id,))
    conn.close()

    if df.empty:
        print("No evaluation data found for this run.")
        return

    config.ensure_dirs()
    output_dir = Path(config.research_output_dir)

    # 1. Accuracy vs Evidence Level
    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=df, 
        x="evidence_level", 
        y="cpe_accurate", 
        order=["E4", "E3", "E2", "E1", "E0"],
        errorbar=None,
        hue="evidence_level",
        palette="viridis",
        legend=False
    )
    plt.title("CPE Accuracy vs Evidence Level")
    plt.ylabel("Accuracy (0.0 to 1.0)")
    plt.xlabel("Evidence Level")
    plt.ylim(0, 1)
    plt.savefig(output_dir / "accuracy_vs_evidence.png")
    plt.close()
    
    # 2. Abstention Rate vs Evidence Level
    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=df, 
        x="evidence_level", 
        y="abstained", 
        order=["E4", "E3", "E2", "E1", "E0"],
        errorbar=None,
        hue="evidence_level",
        palette="magma",
        legend=False
    )
    plt.title("Abstention Rate vs Evidence Level")
    plt.ylabel("Abstention Rate (0.0 to 1.0)")
    plt.xlabel("Evidence Level")
    plt.ylim(0, 1)
    plt.savefig(output_dir / "abstention_vs_evidence.png")
    plt.close()

    # 3. Confidence vs Evidence Level
    plt.figure(figsize=(10, 6))
    sns.boxplot(
        data=df, 
        x="evidence_level", 
        y="confidence", 
        order=["E4", "E3", "E2", "E1", "E0"],
        hue="evidence_level",
        palette="crest",
        legend=False
    )
    plt.title("Model Confidence vs Evidence Level")
    plt.ylabel("Confidence (0.0 to 1.0)")
    plt.xlabel("Evidence Level")
    plt.ylim(0, 1)
    plt.savefig(output_dir / "confidence_vs_evidence.png")
    plt.close()

    print(f"Figures saved to {output_dir}")

if __name__ == "__main__":
    generate_all_figures()
