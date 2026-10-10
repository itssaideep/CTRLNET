import asyncio
import logging
from typing import Dict, Any, List, Callable, Awaitable

import nmap

from ctrlnet.config import config
from ctrlnet.scanner.evidence_extractor import extract_evidence, EvidenceRecord

logger = logging.getLogger(__name__)

class NetworkScanner:
    """Wraps python-nmap for async network scanning."""
    
    def __init__(self, event_callback: Callable[[str, Dict[str, Any]], Awaitable[None]] = None):
        """
        Initialize the scanner.
        :param event_callback: Async function to call with real-time events.
        """
        try:
            self.scanner = nmap.PortScanner(nmap_search_path=[config.nmap_path, 'nmap', '/usr/bin/nmap', '/usr/local/bin/nmap'])
        except nmap.PortScannerError as e:
            logger.error(f"Nmap not found: {e}. Please ensure Nmap is installed.")
            raise
            
        self.event_callback = event_callback

    async def _emit(self, event_name: str, payload: Dict[str, Any]):
        """Emit an event if a callback is registered."""
        if self.event_callback:
            try:
                await self.event_callback(event_name, payload)
            except Exception as e:
                logger.error(f"Error emitting event {event_name}: {e}")

    async def scan_target(self, target: str, ports: str = None) -> List[EvidenceRecord]:
        """
        Scan a target IP or hostname and extract evidence.
        Runs the blocking nmap scan in a thread pool to avoid blocking the event loop.
        """
        ports = ports or config.nmap_default_ports
        args = config.nmap_arguments
        
        await self._emit("scan_started", {"target": target, "ports": ports})
        
        logger.info(f"Starting Nmap scan against {target} with args: {args}")
        
        # Run blocking nmap call in a thread
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(
                None, 
                lambda: self.scanner.scan(hosts=target, ports=ports, arguments=args, timeout=config.nmap_timeout)
            )
        except Exception as e:
            logger.error(f"Nmap scan failed: {e}")
            await self._emit("scan_failed", {"target": target, "error": str(e)})
            return []

        evidence_records = []

        for host in self.scanner.all_hosts():
            host_state = self.scanner[host].state()
            if host_state != 'up':
                continue
                
            await self._emit("host_discovered", {"host": host, "state": host_state})
            
            # Try to get OS hint
            os_hint = None
            if 'osmatch' in self.scanner[host] and len(self.scanner[host]['osmatch']) > 0:
                os_hint = self.scanner[host]['osmatch'][0]['name']

            # Iterate through protocols (usually 'tcp')
            for proto in self.scanner[host].all_protocols():
                port_keys = self.scanner[host][proto].keys()
                for port in port_keys:
                    port_data = self.scanner[host][proto][port]
                    
                    if port_data['state'] != 'open':
                        continue
                        
                    await self._emit("service_found", {
                        "host": host, 
                        "port": port, 
                        "service": port_data.get('name', 'unknown')
                    })
                    
                    # Extract evidence
                    evidence = extract_evidence(
                        nmap_service_data=port_data,
                        port=port,
                        target_id=host,
                        os_hint=os_hint
                    )
                    evidence_records.append(evidence)
                    
                    await self._emit("evidence_extracted", {
                        "host": host,
                        "port": port,
                        "evidence": evidence.model_dump()
                    })

        await self._emit("scan_complete", {"target": target, "services_found": len(evidence_records)})
        return evidence_records
