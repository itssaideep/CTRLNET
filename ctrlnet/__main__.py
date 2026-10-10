import sys
import uvicorn
from pathlib import Path
from ctrlnet.config import config

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m ctrlnet [serve|scan|research]")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "serve":
        print(f"Starting CTRLNET Server on {config.server_host}:{config.server_port}")
        # Run uvicorn programmatically
        uvicorn.run(
            "ctrlnet.server.live_server:app", 
            host=config.server_host, 
            port=config.server_port, 
            reload=False
        )
        
    elif command == "scan":
        if len(sys.argv) < 3:
            print("Usage: python -m ctrlnet scan <target> [model]")
            sys.exit(1)
        target = sys.argv[2]
        model = sys.argv[3] if len(sys.argv) > 3 else None
        
        async def run_cli_scan(t, m):
            from ctrlnet.scanner.network_scanner import NetworkScanner
            from ctrlnet.hybrid.hybrid_analyzer import HybridAnalyzer
            import json
            
            async def print_event(event_name, payload):
                # Format output nicely for CLI
                if event_name in ["scan_started", "scan_complete", "host_discovered", "service_found", "llm_analysis_started", "service_complete"]:
                    print(f"[*] {event_name.upper()}: {payload}")
                elif event_name == "llm_response":
                    pred = payload.get("prediction", {})
                    print(f"  [+] LLM Hypothesis: {pred.get('cpe')} (Confidence: {pred.get('confidence')})")
                elif event_name == "verification_done":
                    res = payload.get("results", {})
                    print(f"  [+] Verification: CPE Valid={res.get('cpe_valid')}, Stats={res.get('summary')}")
            
            print(f"Starting CLI scan for {t}...")
            scanner = NetworkScanner(event_callback=print_event)
            analyzer = HybridAnalyzer(event_callback=print_event)
            
            evidence_records = await scanner.scan_target(t)
            if not evidence_records:
                print("No services found or scan failed.")
                return
                
            for evidence in evidence_records:
                print(f"\n--- Analyzing {evidence.target_id}:{evidence.port} ({evidence.service}) ---")
                await analyzer.run_hybrid_pipeline(evidence, model=m)
                
            print("\nScan and analysis complete.")
                
        import asyncio
        asyncio.run(run_cli_scan(target, model))
        
    elif command == "research":
        print("Starting research pipeline...")
        import asyncio
        from ctrlnet.research.research_pipeline import run_experiment
        asyncio.run(run_experiment())
        
    else:
        print(f"Unknown command: {command}")
        
if __name__ == "__main__":
    main()
