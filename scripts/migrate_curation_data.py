"""
Data Migration Script for Policy Curation
Migrates BHSA policy manual and W&I Code statutes from prototype to production
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agents.knowledge.knowledge_base import DHCSKnowledgeBase
from agents.knowledge.curation_loader import CurationDocumentLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_policy_manual(manual_path: str) -> int:
    """
    Migrate BHSA County Policy Manual to production knowledge base.

    Args:
        manual_path: Path to BHSA_County_Policy_Manual.md

    Returns:
        Number of document chunks added
    """
    logger.info("=" * 80)
    logger.info("STEP 1: Migrating Policy Manual")
    logger.info("=" * 80)

    kb = DHCSKnowledgeBase()
    loader = CurationDocumentLoader(kb)

    chunks_added = loader.load_policy_manual(manual_path)

    logger.info(f"✓ Policy manual migration complete: {chunks_added} chunks added")

    return chunks_added


def migrate_statutes(statute_path: str = None) -> int:
    """
    Migrate W&I Code statutes to production knowledge base.

    Args:
        statute_path: Optional path to statute markdown file

    Returns:
        Number of statute chunks added
    """
    logger.info("=" * 80)
    logger.info("STEP 2: Migrating W&I Code Statutes")
    logger.info("=" * 80)

    kb = DHCSKnowledgeBase()
    loader = CurationDocumentLoader(kb)

    if statute_path:
        logger.info(f"Loading statutes from: {statute_path}")
        chunks_added = loader.load_statute_catalog(statute_markdown_path=statute_path)
    else:
        logger.warning("No statute file provided - loading placeholders")
        logger.warning("You should replace these with actual statute texts later")
        chunks_added = loader.load_statute_catalog()

    logger.info(f"✓ Statute migration complete: {chunks_added} chunks added")

    return chunks_added


def verify_migration() -> dict:
    """
    Verify that documents were migrated correctly.

    Returns:
        Statistics about migrated documents
    """
    logger.info("=" * 80)
    logger.info("STEP 3: Verifying Migration")
    logger.info("=" * 80)

    kb = DHCSKnowledgeBase()
    loader = CurationDocumentLoader(kb)

    stats = loader.verify_loading()

    logger.info("Migration Verification Results:")
    logger.info(f"  Total Documents: {stats['total_documents']}")
    logger.info(f"  Policy Documents: {stats.get('policy_documents', 'unknown')}")
    logger.info(f"  Statute Documents: {stats.get('statute_documents', 'unknown')}")
    logger.info(f"  Collection: {stats['collection_name']}")

    return stats


def test_retrieval():
    """
    Test that retrieval works correctly with migrated documents.
    """
    logger.info("=" * 80)
    logger.info("STEP 4: Testing Retrieval")
    logger.info("=" * 80)

    kb = DHCSKnowledgeBase()

    # Test policy retrieval
    logger.info("Testing policy retrieval...")
    policy_results = kb.search("workforce requirements for BHSA providers", n_results=3)

    if policy_results:
        logger.info(f"✓ Policy retrieval working: Found {len(policy_results)} results")
        logger.info(f"  Top result: {policy_results[0]['content'][:100]}...")
    else:
        logger.warning("⚠ Policy retrieval returned no results")

    # Test statute retrieval
    logger.info("Testing statute retrieval...")
    statute_results = kb.search("W&I Code requirements documentation", n_results=3)

    if statute_results:
        logger.info(f"✓ Statute retrieval working: Found {len(statute_results)} results")
        logger.info(f"  Top result: {statute_results[0]['content'][:100]}...")
    else:
        logger.warning("⚠ Statute retrieval returned no results")


def main():
    """
    Main migration workflow.

    Usage:
        python scripts/migrate_curation_data.py

    Prerequisites:
        1. Copy BHSA_County_Policy_Manual.md to data/ directory
        2. (Optional) Copy statute texts to data/statutes.md
        3. Set OPENAI_API_KEY environment variable
    """
    logger.info("=" * 80)
    logger.info("POLICY CURATION DATA MIGRATION")
    logger.info("=" * 80)
    logger.info("")

    # Define paths (relative to dhcs-intake-lab root)
    data_dir = Path(__file__).parent.parent / "data"
    policy_manual_path = data_dir / "BHSA_County_Policy_Manual.md"
    statute_path = data_dir / "statutes.md"  # Optional

    # Check if policy manual exists
    if not policy_manual_path.exists():
        logger.error(f"❌ Policy manual not found: {policy_manual_path}")
        logger.error("")
        logger.error("Please copy the policy manual:")
        logger.error(f"  cp /Users/raj/work/workspace/dhcs/agent-boiler-plate/src/rag_curation/data/BHSA_County_Policy_Manual.md {policy_manual_path}")
        logger.error("")
        return 1

    try:
        # Step 1: Migrate policy manual
        policy_chunks = migrate_policy_manual(str(policy_manual_path))

        # Step 2: Migrate statutes
        if statute_path.exists():
            statute_chunks = migrate_statutes(str(statute_path))
        else:
            logger.warning(f"Statute file not found: {statute_path}")
            logger.warning("Loading placeholder statutes instead")
            statute_chunks = migrate_statutes()

        # Step 3: Verify migration
        stats = verify_migration()

        # Step 4: Test retrieval
        test_retrieval()

        # Summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("MIGRATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"✓ Policy chunks added: {policy_chunks}")
        logger.info(f"✓ Statute chunks added: {statute_chunks}")
        logger.info(f"✓ Total documents: {stats['total_documents']}")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Start the API: docker-compose up -d")
        logger.info("  2. Test curation endpoint: curl http://localhost:8000/curation/stats")
        logger.info("  3. Process a test question via API or Streamlit UI")
        logger.info("")

        return 0

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
