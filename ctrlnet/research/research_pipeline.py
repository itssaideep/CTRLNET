import logging
import asyncio
from datetime import datetime

from ctrlnet.config import config, EvidenceLevel, ExperimentCondition
from ctrlnet.database.database import db_manager
from ctrlnet.corpus.blind_spot_corpus import BlindSpotCorpus
from ctrlnet.hybrid.hybrid_analyzer import HybridAnalyzer
from ctrlnet.evaluation.scorer import Scorer
from ctrlnet.evaluation.failure_classifier import FailureClassifier
from ctrlnet.llm.schemas import LLMPrediction

logger = logging.getLogger(__name__)

async def run_experiment():
    """Runs a batch experiment over the corpus and saves results."""
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"Starting experiment run: {run_id}")
    
    # Init DB
    await db_manager.initialize_schema()
    
    # Config
    model = config.ollama_model
    condition = ExperimentCondition.HYBRID.value
    
    await db_manager.create_experiment_config(
        run_id=run_id,
        dataset_version="1.0",
        model=model,
        prompt_version="v1",
        temperature=config.ollama_temperature,
        condition=condition
    )
    
    corpus = BlindSpotCorpus()
    targets = corpus.load_all_targets()
    
    analyzer = HybridAnalyzer()
    
    for target in targets:
        target_id = target['target_id']
        logger.info(f"Processing target: {target_id}")
        
        # Ensure target is in DB
        await db_manager.execute(
            "INSERT OR IGNORE INTO targets (id) VALUES (?)", 
            (target_id,)
        )
        
        variants = corpus.generate_variants(target)
        
        for level, evidence in variants.items():
            logger.info(f"  Level: {level}")
            
            # Save evidence
            ev_id = await db_manager.save_evidence(
                run_id=run_id,
                target_id=target_id,
                service=evidence.service,
                port=evidence.port,
                evidence_level=level,
                raw_banner=evidence.raw_banner,
                extracted_product=evidence.extracted_product,
                extracted_version=evidence.extracted_version
            )
            
            # Analyze
            result = await analyzer.run_hybrid_pipeline(evidence, model=model)
            
            # Save Prediction
            llm_hyp = result.get('llm_hypothesis')
            if llm_hyp:
                pred = llm_hyp['prediction']
                metrics = llm_hyp['metrics']
                
                # Parse back to Pydantic object for scorer
                pred_obj = LLMPrediction(**pred)
                
                # Save prediction
                pred_id = await db_manager.save_prediction(
                    evidence_id=ev_id,
                    source="LLM",
                    service=pred.get('service'),
                    product=pred.get('product'),
                    version=pred.get('version'),
                    cpe=pred.get('cpe'),
                    cves=[c.get('id') for c in pred.get('cves', [])] if pred.get('cves') else [],
                    confidence=pred.get('confidence', 0.0),
                    abstained=pred.get('abstain', False),
                    latency_ms=metrics.get('latency_ms', 0.0),
                    raw_output=llm_hyp.get('raw_output')
                )
                
                # Score prediction
                scores = Scorer.score_prediction(pred_obj, target)
                failure_cat = FailureClassifier.classify(pred_obj, scores, target)
                
                await db_manager.save_evaluation(
                    prediction_id=pred_id,
                    verdict=result['final_status'],
                    failure_category=failure_cat.value if failure_cat else None,
                    product_accurate=scores['product_accurate'],
                    version_accurate=scores['version_accurate'],
                    cpe_accurate=scores['cpe_accurate'],
                    cve_precision=scores['cve_precision'],
                    cve_recall=scores['cve_recall'],
                    cve_f1=scores['cve_f1']
                )
                
                logger.info(f"    Verdict: {result['final_status']} | Accuracy: {scores['cpe_accurate']}")
                
    logger.info(f"Experiment {run_id} complete.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_experiment())
