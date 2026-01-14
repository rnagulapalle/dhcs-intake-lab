"""
Curation Document Loader
Migrates BHSA policy manual and W&I Code statutes from prototype to production
"""
import logging
import re
from typing import List, Dict, Any
from pathlib import Path

from agents.knowledge.knowledge_base import DHCSKnowledgeBase
from agents.core.config import settings

logger = logging.getLogger(__name__)


class CurationDocumentLoader:
    """
    Loads policy curation documents into ChromaDB with enhanced metadata.

    Improvements over prototype:
    - Excludes TOC sections
    - Adds rich metadata (section, category, version)
    - Better chunking strategy (1500 chars, 300 overlap)
    - Metadata-based filtering capability
    """

    def __init__(self, kb: DHCSKnowledgeBase = None):
        self.kb = kb or DHCSKnowledgeBase(persist_directory=settings.chroma_persist_dir)

        # Exclusion patterns for filtering out non-content sections
        self.exclusion_patterns = [
            r"^Table of Contents",
            r"^Behavioral Health Services Act County Policy Manual$",
            r"^Version \d+\.\d+\.\d+",
            r"^##\s*Table of Contents",
        ]

        logger.info("CurationDocumentLoader initialized")

    def load_policy_manual(self, markdown_path: str) -> int:
        """
        Load BHSA County Policy Manual with improved chunking and metadata.

        Args:
            markdown_path: Path to BHSA_County_Policy_Manual.md

        Returns:
            Number of document chunks added

        Improvements over prototype:
        - Chunk size: 1500 chars (vs 2000)
        - Overlap: 300 chars (vs 500)
        - Metadata: category, section, version
        - Exclusions: TOC and boilerplate
        """
        logger.info(f"Loading policy manual from {markdown_path}")

        path = Path(markdown_path)
        if not path.exists():
            raise FileNotFoundError(f"Policy manual not found: {markdown_path}")

        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract version
        version = self._extract_version(content)
        logger.info(f"Detected policy manual version: {version}")

        # Split by major sections (##)
        sections = self._split_by_sections(content)
        logger.info(f"Found {len(sections)} sections in policy manual")

        all_docs = []
        excluded_count = 0

        for section_title, section_content in sections:
            # Skip excluded sections
            if self._should_exclude(section_title):
                logger.debug(f"Excluding section: {section_title}")
                excluded_count += 1
                continue

            # Chunk section content with improved parameters
            chunks = self._chunk_text(section_content)

            for i, chunk in enumerate(chunks):
                doc = {
                    "id": f"policy_{self._slugify(section_title)}_chunk_{i}",
                    "content": chunk,
                    "metadata": {
                        "source": "BHSA County Policy Manual",
                        "section": section_title,
                        "category": "policy",
                        "version": version,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "doc_type": "policy_manual"
                    }
                }
                all_docs.append(doc)

        logger.info(
            f"Created {len(all_docs)} policy document chunks "
            f"(excluded {excluded_count} sections)"
        )

        # Add to ChromaDB
        self.kb.add_documents(all_docs)

        logger.info("Policy manual loaded successfully")

        return len(all_docs)

    def load_statute_catalog(
        self,
        statute_texts: Dict[str, str] = None,
        statute_markdown_path: str = None
    ) -> int:
        """
        Load W&I Code statutes with metadata.

        Args:
            statute_texts: Dict mapping citations to full text
                Example: {"W&I Code § 5899": "full statute text..."}
            statute_markdown_path: Alternative - path to markdown file with statutes

        Returns:
            Number of statute chunks added

        Note: If you don't have statute texts yet, this creates placeholder
        documents that will be populated later.
        """
        logger.info("Loading W&I Code statutes")

        all_docs = []

        if statute_markdown_path:
            # Load from markdown file
            statute_texts = self._parse_statute_markdown(statute_markdown_path)

        elif statute_texts is None:
            # Create placeholder documents for statute catalog
            logger.warning(
                "No statute texts provided. Creating placeholder documents. "
                "Update these with actual statute content later."
            )
            statute_texts = self._get_placeholder_statutes()

        for citation, text in statute_texts.items():
            # Chunk long statutes
            chunks = self._chunk_text(text)

            for i, chunk in enumerate(chunks):
                doc = {
                    "id": f"statute_{self._slugify(citation)}_chunk_{i}",
                    "content": chunk,
                    "metadata": {
                        "source": citation,
                        "category": "statute",
                        "type": "W&I Code",
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "doc_type": "statute"
                    }
                }
                all_docs.append(doc)

        logger.info(f"Created {len(all_docs)} statute chunks from {len(statute_texts)} statutes")

        # Add to ChromaDB
        self.kb.add_documents(all_docs)

        logger.info("Statutes loaded successfully")

        return len(all_docs)

    def _split_by_sections(self, content: str) -> List[tuple]:
        """
        Split markdown by ## headers.

        Returns list of (title, content) tuples.
        """
        sections = []
        pattern = r'^## (.+?)$'
        matches = list(re.finditer(pattern, content, re.MULTILINE))

        for i, match in enumerate(matches):
            title = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            section_content = content[start:end].strip()
            sections.append((title, section_content))

        return sections

    def _should_exclude(self, section_title: str) -> bool:
        """Check if section should be excluded from indexing."""
        for pattern in self.exclusion_patterns:
            if re.match(pattern, section_title, re.IGNORECASE):
                return True
        return False

    def _chunk_text(self, text: str) -> List[str]:
        """
        Chunk text with improved parameters.

        Uses 1500 char chunks with 300 overlap (vs prototype's 2000/500).
        Better preserves context while reducing retrieval noise.
        """
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True,
            length_function=len
        )

        return splitter.split_text(text)

    def _extract_version(self, content: str) -> str:
        """Extract version number from policy manual."""
        match = re.search(r'Version (\d+\.\d+\.\d+)', content)
        return match.group(1) if match else "unknown"

    def _slugify(self, text: str) -> str:
        """Convert text to slug for IDs."""
        # Remove special characters, convert to lowercase, replace spaces with underscores
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '_', slug)
        return slug[:50]  # Limit length

    def _parse_statute_markdown(self, markdown_path: str) -> Dict[str, str]:
        """
        Parse statute texts from markdown file.

        Expected format:
        ## W&I Code § 5899
        Statute text here...

        ## W&I Code § 14184
        Statute text here...
        """
        logger.info(f"Parsing statutes from {markdown_path}")

        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()

        statute_texts = {}

        # Pattern to match statute headers
        pattern = r'^## (W&I Code .*?)$'
        matches = list(re.finditer(pattern, content, re.MULTILINE))

        for i, match in enumerate(matches):
            citation = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            statute_text = content[start:end].strip()

            statute_texts[citation] = statute_text

        logger.info(f"Parsed {len(statute_texts)} statutes from markdown")

        return statute_texts

    def _get_placeholder_statutes(self) -> Dict[str, str]:
        """
        Get placeholder statute texts for initial setup.

        These should be replaced with actual statute content later.
        """
        statute_catalog = [
            "W&I Code § 5899",
            "W&I Code § 14184",
            "W&I Code § 5892",
            "W&I Code § 5891",
            "W&I Code § 5830",
            "W&I Code § 14018",
            "W&I Code § 5840",
            "W&I Code § 8255",
            "W&I Code § 5963",
            "W&I Code § 8256",
            "W&I Code § 5604",
            "W&I Code § 14124",
            "W&I Code § 14197",
            "W&I Code § 5600",
            "W&I Code § 5835",
            "W&I Code § 5964",
            "W&I Code § 5350",
            "W&I Code § 5887"
        ]

        placeholders = {}

        for citation in statute_catalog:
            placeholders[citation] = (
                f"{citation}\n\n"
                f"[Placeholder - Replace with actual statute text]\n\n"
                f"This is a placeholder for {citation}. "
                f"The actual statute text should be obtained from California Legislative Information "
                f"(https://leginfo.legislature.ca.gov) and loaded here."
            )

        return placeholders

    def verify_loading(self) -> Dict[str, Any]:
        """
        Verify that documents were loaded correctly.

        Returns statistics about the loaded documents.
        """
        logger.info("Verifying document loading")

        total_docs = self.kb.collection.count()

        # Try to query for specific categories
        try:
            policy_results = self.kb.collection.query(
                query_texts=["test"],
                n_results=1,
                where={"category": "policy"}
            )
            policy_count = len(policy_results.get("documents", [[]])[0])
        except:
            policy_count = 0

        try:
            statute_results = self.kb.collection.query(
                query_texts=["test"],
                n_results=1,
                where={"category": "statute"}
            )
            statute_count = len(statute_results.get("documents", [[]])[0])
        except:
            statute_count = 0

        stats = {
            "total_documents": total_docs,
            "policy_documents": policy_count,
            "statute_documents": statute_count,
            "collection_name": self.kb.collection.name
        }

        logger.info(f"Verification complete: {stats}")

        return stats
