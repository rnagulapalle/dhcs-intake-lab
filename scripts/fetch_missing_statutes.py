"""
Statute Data Acquisition Tool
Fetches missing W&I Code statutes from California Legislative Information website.

Safety Features:
- Read-only operations (no modification of existing data)
- Validation before saving
- Backup creation
- Dry-run mode
"""
import re
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import urllib.request
import urllib.parse
import urllib.error

# Missing statute sections (identified from placeholder analysis)
MISSING_STATUTES = [
    "5600",
    "5600.2",
    "5651",
    "5678",
    "5685",
    "5697",
    "5814",
    "5892",
    "5897",
    "14043.26",
    "14021",
    "14124",
    "14124.24",
    "14124.25",
    "14680.5"
]

# California Legislative Information base URL
LEGINFO_BASE = "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml"

def fetch_statute_from_leginfo(section_number: str) -> Optional[Dict[str, str]]:
    """
    Fetch statute text from California Legislative Information website.

    Args:
        section_number: W&I Code section (e.g., "5600", "14124.24")

    Returns:
        Dict with section_number, title, text, source_url, or None if not found
    """
    # Build URL
    params = {
        "sectionNum": section_number,
        "lawCode": "WIC"  # Welfare and Institutions Code
    }
    url = f"{LEGINFO_BASE}?{urllib.parse.urlencode(params)}"

    print(f"Fetching W&I Code § {section_number}...")
    print(f"URL: {url}")

    try:
        # Fetch page
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (DHCS-Research-Tool)')

        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')

        # Parse HTML to extract statute text
        # The leginfo site has statute text in specific HTML structure
        # This is a simplified parser - may need adjustment based on actual HTML

        # Extract section title (usually in heading)
        title_match = re.search(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
        if title_match:
            title = clean_html(title_match.group(1))
        else:
            # Fallback: use section number as title
            title = f"Section {section_number}"

        # Extract statute text (usually in div with class containing "statute" or "section")
        # Look for common patterns in leginfo HTML
        text_patterns = [
            r'<div[^>]*class="[^"]*statute[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*id="[^"]*content[^"]*"[^>]*>(.*?)</div>',
            r'<p[^>]*>(.*?)</p>',
        ]

        statute_text = None
        for pattern in text_patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            if matches:
                # Concatenate all matches and clean
                statute_text = '\n\n'.join(clean_html(m) for m in matches)
                if len(statute_text) > 100:  # Reasonable minimum length
                    break

        if not statute_text or len(statute_text) < 50:
            print(f"  ⚠️  Could not extract statute text (HTML structure may have changed)")
            return None

        # Validate: check for legal language
        legal_keywords = ['shall', 'must', 'may', 'section', 'subdivision', 'county', 'counties']
        if not any(keyword in statute_text.lower() for keyword in legal_keywords):
            print(f"  ⚠️  Extracted text doesn't appear to be legal statute (no legal keywords)")
            return None

        print(f"  ✅ Successfully fetched {len(statute_text)} characters")

        return {
            "section_number": section_number,
            "title": title,
            "text": statute_text,
            "source_url": url,
            "fetch_date": datetime.now().isoformat()
        }

    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP Error {e.code}: {e.reason}")
        return None
    except urllib.error.URLError as e:
        print(f"  ❌ URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def clean_html(html: str) -> str:
    """Remove HTML tags and clean up text."""
    # Remove script and style tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html)

    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s+', '\n', text)

    # Decode HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")

    return text.strip()

def format_statute_markdown(statute: Dict[str, str]) -> str:
    """Format statute data as markdown for statutes.md file."""
    section = statute["section_number"]
    title = statute["title"]
    text = statute["text"]
    source_url = statute["source_url"]
    fetch_date = statute["fetch_date"]

    # Format as markdown
    md = f"""## W&I Code § {section}: {title}

{text}

**Source**: [California Legislative Information]({source_url})
**Retrieved**: {fetch_date}

---
"""
    return md

def backup_statutes_file():
    """Create backup of existing statutes.md file."""
    statutes_file = Path(__file__).parent.parent / "data" / "statutes.md"

    if not statutes_file.exists():
        print("⚠️  No existing statutes.md file to backup")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = statutes_file.parent / f"statutes_backup_{timestamp}.md"

    # Copy file
    with open(statutes_file, 'r') as f:
        content = f.read()

    with open(backup_file, 'w') as f:
        f.write(content)

    print(f"✅ Backup created: {backup_file}")
    return backup_file

def append_statute_to_file(statute: Dict[str, str], dry_run: bool = False):
    """Append fetched statute to statutes.md file."""
    statutes_file = Path(__file__).parent.parent / "data" / "statutes.md"

    markdown = format_statute_markdown(statute)

    if dry_run:
        print("\n" + "="*80)
        print("DRY RUN - Would append:")
        print("="*80)
        print(markdown)
        print("="*80)
        return

    # Append to file
    with open(statutes_file, 'a') as f:
        f.write("\n" + markdown)

    print(f"✅ Appended W&I Code § {statute['section_number']} to statutes.md")

def remove_placeholder(section_number: str, dry_run: bool = False):
    """Remove placeholder entry for a statute section."""
    statutes_file = Path(__file__).parent.parent / "data" / "statutes.md"

    if not statutes_file.exists():
        return

    with open(statutes_file, 'r') as f:
        content = f.read()

    # Pattern to match placeholder section
    pattern = f"## W&I Code § {section_number}:.*?(?=##|$)"

    # Find placeholder
    matches = list(re.finditer(pattern, content, re.DOTALL))

    if not matches:
        print(f"  ℹ️  No placeholder found for § {section_number}")
        return

    # Check if it's actually a placeholder
    match_text = matches[0].group(0)
    if "[Placeholder" not in match_text:
        print(f"  ℹ️  Section {section_number} already has real content, skipping removal")
        return

    if dry_run:
        print(f"  🔍 DRY RUN - Would remove placeholder for § {section_number}")
        return

    # Remove placeholder
    content = re.sub(pattern, "", content, count=1, flags=re.DOTALL)

    with open(statutes_file, 'w') as f:
        f.write(content)

    print(f"  🗑️  Removed placeholder for § {section_number}")

def main(dry_run: bool = True, max_fetches: int = 5):
    """
    Main function to fetch missing statutes.

    Args:
        dry_run: If True, don't modify files (just preview)
        max_fetches: Maximum number of statutes to fetch (rate limiting)
    """
    print("="*80)
    print("STATUTE DATA ACQUISITION TOOL")
    print("="*80)
    print(f"Mode: {'DRY RUN (no files modified)' if dry_run else 'LIVE (will modify files)'}")
    print(f"Max fetches: {max_fetches}")
    print(f"Missing statutes to fetch: {len(MISSING_STATUTES)}")
    print("="*80)

    if not dry_run:
        # Create backup before modifying
        backup_file = backup_statutes_file()
        if backup_file:
            print(f"Backup created at: {backup_file}")

    # Fetch statutes
    fetched_count = 0
    failed_count = 0

    for section_number in MISSING_STATUTES[:max_fetches]:
        if fetched_count >= max_fetches:
            print(f"\n⏸️  Reached max fetch limit ({max_fetches})")
            break

        print(f"\n[{fetched_count + 1}/{max_fetches}] Processing § {section_number}...")

        # Fetch from legislative website
        statute = fetch_statute_from_leginfo(section_number)

        if statute:
            # Remove placeholder
            remove_placeholder(section_number, dry_run=dry_run)

            # Append new statute
            append_statute_to_file(statute, dry_run=dry_run)

            fetched_count += 1

            # Rate limiting - be respectful to the server
            if not dry_run and fetched_count < max_fetches:
                print("  ⏱️  Waiting 5 seconds before next request...")
                time.sleep(5)
        else:
            failed_count += 1

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Successfully fetched: {fetched_count}")
    print(f"Failed: {failed_count}")
    print(f"Remaining: {len(MISSING_STATUTES) - fetched_count - failed_count}")

    if dry_run:
        print("\n⚠️  DRY RUN MODE - No files were modified")
        print("To actually fetch and save statutes, run:")
        print("  python3 scripts/fetch_missing_statutes.py --live")
    else:
        print("\n✅ Statutes saved to data/statutes.md")
        print("Next steps:")
        print("  1. Review the fetched statutes in data/statutes.md")
        print("  2. Clear ChromaDB: docker volume rm dhcs-intake-lab_chroma_data")
        print("  3. Rebuild API: docker-compose up -d --build agent-api")
        print("  4. Migrate data: docker-compose exec agent-api python scripts/migrate_curation_data.py")

    print("="*80)

if __name__ == "__main__":
    import sys

    # Parse arguments
    dry_run = True
    max_fetches = 3  # Start with just 3 for safety

    if "--live" in sys.argv:
        dry_run = False
        print("⚠️  LIVE MODE - Files will be modified!")
        confirm = input("Are you sure? Type 'yes' to continue: ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)

    if "--all" in sys.argv:
        max_fetches = len(MISSING_STATUTES)
    elif "--max" in sys.argv:
        idx = sys.argv.index("--max")
        if idx + 1 < len(sys.argv):
            max_fetches = int(sys.argv[idx + 1])

    # Run
    main(dry_run=dry_run, max_fetches=max_fetches)
