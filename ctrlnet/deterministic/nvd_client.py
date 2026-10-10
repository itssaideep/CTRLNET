import asyncio
import logging
from typing import List, Dict, Any, Optional

import nvdlib
import requests

from ctrlnet.config import config
from ctrlnet.database.database import db_manager

logger = logging.getLogger(__name__)

class NVDClient:
    """Client for querying the NVD API for CVEs based on CPEs."""

    def __init__(self):
        self.api_key = config.nvd_api_key
        self.rate_limit = config.effective_rate_limit
        self.last_request_time = 0.0
        self._lock = asyncio.Lock()

    async def _wait_for_rate_limit(self):
        """Ensure we don't exceed NVD API rate limits."""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self.last_request_time
            if elapsed < self.rate_limit:
                await asyncio.sleep(self.rate_limit - elapsed)
            self.last_request_time = asyncio.get_event_loop().time()

    async def search_cve(self, cpe_name: str) -> List[Dict[str, Any]]:
        """
        Search for CVEs associated with a specific CPE.
        Uses caching to avoid redundant API calls.
        """
        # 1. Check Cache
        cached_cves = await db_manager.get_cached_cves(cpe_name)
        if cached_cves is not None:
            logger.info(f"NVD cache hit for {cpe_name}")
            return cached_cves

        # 2. Query API
        logger.info(f"Querying NVD API for {cpe_name}")
        await self._wait_for_rate_limit()

        cves = []
        try:
            # Run blocking nvdlib call in a thread
            loop = asyncio.get_running_loop()
            
            def do_search():
                kwargs = {'cpeName': cpe_name}
                if self.api_key:
                    kwargs['key'] = self.api_key
                return list(nvdlib.searchCVE(**kwargs))

            results = await loop.run_in_executor(None, do_search)
            
            for cve_obj in results:
                # Extract relevant fields from the nvdlib object
                description = ""
                for desc in cve_obj.descriptions:
                    if getattr(desc, 'lang', '') == 'en':
                         description = getattr(desc, 'value', '')
                         break
                         
                cves.append({
                    "id": cve_obj.id,
                    "description": description,
                    "published": getattr(cve_obj, 'published', ''),
                    "v3_score": getattr(cve_obj.v31score, 'baseScore', None) if hasattr(cve_obj, 'v31score') else None
                })
                
        except Exception as e:
            logger.error(f"Failed to fetch CVEs from NVD for {cpe_name}: {e}")
            # Consider if we want to return [] or raise on failure. 
            # Returning [] might poison the cache if we cache it.
            return []

        # 3. Cache Results
        await db_manager.cache_cves(cpe_name, cves)
        return cves
        
    async def verify_cve(self, cve_id: str) -> bool:
        """Verify if a CVE ID exists in the NVD."""
        await self._wait_for_rate_limit()
        try:
             loop = asyncio.get_running_loop()
             def do_search():
                 kwargs = {'cveId': cve_id}
                 if self.api_key:
                     kwargs['key'] = self.api_key
                 return list(nvdlib.searchCVE(**kwargs))
                 
             results = await loop.run_in_executor(None, do_search)
             return len(results) > 0
        except Exception as e:
             logger.error(f"Failed to verify CVE {cve_id}: {e}")
             return False
