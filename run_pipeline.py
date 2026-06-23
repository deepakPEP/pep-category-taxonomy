import sys
import time
from common.logger import get_logger
from common.metrics import save_metrics

logger = get_logger("pipeline")

def main():
    logger.info("=" * 60)
    logger.info("B2B TAXONOMY PIPELINE STARTING")
    logger.info("=" * 60)

    start = time.time()

    try:
        logger.info(">>> Phase 1: Batch Generator")
        from phase1_batch_generator import run as phase1
        phase1()

        logger.info(">>> Phase 2: Qwen Taxonomy Architect")
        from phase2_reorganizer import run as phase2
        phase2()

        logger.info(">>> Phase 2B: Taxonomy Corrector")
        from phase2b_corrector import run as phase2b
        phase2b()

        logger.info(">>> Phase 3: BGE Embeddings + FAISS")
        from phase3_embeddings import run as phase3
        phase3()

        logger.info(">>> Phase 4: Qwen Synonym Merge")
        from phase4_normalizer import run as phase4
        phase4()

        logger.info(">>> Phase 5: Validator")
        from phase5_validator import run as phase5
        phase5()

    except Exception as ex:
        logger.exception(f"Pipeline failed: {ex}")
        sys.exit(1)

    elapsed = round((time.time() - start) / 60, 2)
    logger.info("=" * 60)
    logger.info(f"PIPELINE COMPLETE in {elapsed} minutes")
    logger.info("Output: output/phase5/final_taxonomy.csv")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
