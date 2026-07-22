"""Search Index Service for receipt full-text search.

Implements RULE-BE-017: Search index update for confirmed receipts.
Implements RULE-FLOW-001-14: Search index reflection for confirmed receipts.
Implements RULE-GEN-020: Type hints on all Python code.
Implements RULE-GEN-021: Single responsibility principle.

Uses SQLite FTS5 virtual table for full-text search capability.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
if TYPE_CHECKING:
    from app.api.v1.dependencies import get_db_session_dep

if TYPE_CHECKING:
    from app.models.receipt import Receipt

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Search result item.

    Attributes:
        receipt_id: Receipt ID.
        score: Relevance score (higher is better).
        store_name: Store name.
        total_amount: Total amount.
        receipt_date: Receipt date.
        category: Category name.
        tags: List of tags.
        snippet: Text snippet highlighting match.
    """

    receipt_id: int
    score: float
    store_name: str | None
    total_amount: int | None
    receipt_date: datetime | None
    category: str | None
    tags: list[str]
    snippet: str


@dataclass(frozen=True, slots=True)
class SearchIndexStats:
    """Search index statistics.

    Attributes:
        total_documents: Total indexed documents.
        last_updated: Last update timestamp.
        index_size_bytes: Approximate index size.
    """

    total_documents: int
    last_updated: datetime | None
    index_size_bytes: int


class SearchIndexService:
    """Service for managing SQLite FTS5 search index.

    Single responsibility: Maintain search index for receipt full-text search.
    Uses SQLite FTS5 virtual table for efficient text search.
    """

    FTS_TABLE_NAME = "receipts_fts"
    FTS_TABLE_SQL = f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS {FTS_TABLE_NAME} USING fts5(
            receipt_id UNINDEXED,
            store_name,
            ocr_text,
            ai_comment,
            tags,
            category_name,
            tokenize='unicode61 remove_diacritics 1'
        )
    """

    # Triggers for automatic sync with receipts table
    # Note: tags and category_name require joins, so triggers use subqueries
    TRIGGER_INSERT_SQL = f"""
        CREATE TRIGGER IF NOT EXISTS receipts_ai AFTER INSERT ON receipts BEGIN
            INSERT INTO {FTS_TABLE_NAME} (receipt_id, store_name, ocr_text, ai_comment, tags, category_name)
            VALUES (
                NEW.id,
                COALESCE(NEW.store_name, ''),
                COALESCE(NEW.ocr_text, ''),
                COALESCE(NEW.ai_comment, ''),
                (SELECT group_concat(t.name, ',') FROM receipt_tags rt JOIN tags t ON rt.tag_id = t.id WHERE rt.receipt_id = NEW.id),
                (SELECT c.name FROM categories c WHERE c.id = NEW.category_id)
            );
        END;
    """

    TRIGGER_UPDATE_SQL = f"""
        CREATE TRIGGER IF NOT EXISTS receipts_au AFTER UPDATE ON receipts BEGIN
            UPDATE {FTS_TABLE_NAME}
            SET
                store_name = COALESCE(NEW.store_name, ''),
                ocr_text = COALESCE(NEW.ocr_text, ''),
                ai_comment = COALESCE(NEW.ai_comment, ''),
                tags = (SELECT group_concat(t.name, ',') FROM receipt_tags rt JOIN tags t ON rt.tag_id = t.id WHERE rt.receipt_id = NEW.id),
                category_name = (SELECT c.name FROM categories c WHERE c.id = NEW.category_id)
            WHERE receipt_id = NEW.id;
        END;
    """

    TRIGGER_DELETE_SQL = f"""
        CREATE TRIGGER IF NOT EXISTS receipts_ad AFTER DELETE ON receipts BEGIN
            DELETE FROM {FTS_TABLE_NAME} WHERE receipt_id = OLD.id;
        END;
    """

    def __init__(self, session) -> None:
        """Initialize search index service.

        Args:
            session: Database session.
        """
        self._session = session
        self._settings = get_settings()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize FTS5 table and triggers if not exists."""
        if self._initialized:
            return

        try:
            # Create FTS5 virtual table
            await self._session.execute(text(self.FTS_TABLE_SQL))

            # Create triggers for automatic sync
            await self._session.execute(text(self.TRIGGER_INSERT_SQL))
            await self._session.execute(text(self.TRIGGER_UPDATE_SQL))
            await self._session.execute(text(self.TRIGGER_DELETE_SQL))

            await self._session.commit()
            self._initialized = True

            logger.info("Search index initialized", extra={"table": self.FTS_TABLE_NAME})

        except Exception as e:
            logger.exception("Failed to initialize search index", extra={"error": str(e)})
            raise

    async def index_receipt(self, receipt: "Receipt") -> bool:
        """Add or update a receipt in the search index.

        Args:
            receipt: Receipt to index.

        Returns:
            True if successful.
        """
        await self.initialize()

        try:
            # Prepare tags as comma-separated string
            tags_str = ",".join(receipt.tags) if receipt.tags else ""

            # Get category name (join with categories table)
            category_name = ""
            if receipt.category_id is not None:
                result = await self._session.execute(
                    text("SELECT name FROM categories WHERE id = :id"),
                    {"id": receipt.category_id},
                )
                cat = result.scalar_one_or_none()
                if cat:
                    category_name = cat

            # Upsert into FTS table
            await self._session.execute(
                text(
                    f"""
                    INSERT INTO {self.FTS_TABLE_NAME} (
                        receipt_id, store_name, ocr_text, ai_comment, tags, category_name
                    ) VALUES (
                        :receipt_id, :store_name, :ocr_text, :ai_comment, :tags, :category_name
                    ) ON CONFLICT(receipt_id) DO UPDATE SET
                        store_name = :store_name,
                        ocr_text = :ocr_text,
                        ai_comment = :ai_comment,
                        tags = :tags,
                        category_name = :category_name
                    """
                ),
                {
                    "receipt_id": receipt.id,
                    "store_name": receipt.store_name or "",
                    "ocr_text": receipt.ocr_text or "",
                    "ai_comment": receipt.ai_comment or "",
                    "tags": tags_str,
                    "category_name": category_name,
                },
            )

            await self._session.commit()

            logger.debug(
                "Receipt indexed",
                extra={"receipt_id": receipt.id, "store_name": receipt.store_name},
            )
            return True

        except Exception as e:
            logger.exception(
                "Failed to index receipt",
                extra={"receipt_id": receipt.id, "error": str(e)},
            )
            await self._session.rollback()
            return False

    async def remove_from_index(self, receipt_id: int) -> bool:
        """Remove a receipt from the search index.

        Args:
            receipt_id: Receipt ID to remove.

        Returns:
            True if successful.
        """
        await self.initialize()

        try:
            await self._session.execute(
                text(f"DELETE FROM {self.FTS_TABLE_NAME} WHERE receipt_id = :id"),
                {"id": receipt_id},
            )
            await self._session.commit()

            logger.debug("Receipt removed from index", extra={"receipt_id": receipt_id})
            return True

        except Exception as e:
            logger.exception(
                "Failed to remove receipt from index",
                extra={"receipt_id": receipt_id, "error": str(e)},
            )
            await self._session.rollback()
            return False

    async def search(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        category: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        amount_min: int | None = None,
        amount_max: int | None = None,
    ) -> list[SearchResult]:
        """Search receipts using FTS5 full-text search.

        Args:
            query: Search query string (FTS5 syntax supported).
            limit: Maximum number of results.
            offset: Offset for pagination.
            category: Filter by category.
            date_from: Filter by date from.
            date_to: Filter by date to.
            amount_min: Filter by minimum amount.
            amount_max: Filter by maximum amount.

        Returns:
            List of SearchResult objects.
        """
        await self.initialize()

        try:
            # Build FTS5 query
            fts_query = self._build_fts_query(query)

            # Build SQL with optional filters (join with receipts table for filtering)
            sql = f"""
                SELECT
                    f.receipt_id,
                    f.store_name,
                    f.ocr_text,
                    f.ai_comment,
                    f.tags,
                    f.category_name,
                    r.total_amount,
                    r.receipt_date,
                    r.category_id,
                    r.tags as r_tags,
                    bm25({self.FTS_TABLE_NAME}) as score
                FROM {self.FTS_TABLE_NAME} f
                JOIN receipts r ON r.id = f.receipt_id
                WHERE {self.FTS_TABLE_NAME} MATCH :query
                  AND r.status IN ('approved', 'unapproved')
            """

            params = {"query": fts_query, "limit": limit, "offset": offset}

            # Add filters
            if category:
                sql += " AND r.category_id = (SELECT id FROM categories WHERE name = :category)"
                params["category"] = category

            if date_from:
                sql += " AND r.receipt_date >= :date_from"
                params["date_from"] = date_from

            if date_to:
                sql += " AND r.receipt_date <= :date_to"
                params["date_to"] = date_to

            if amount_min is not None:
                sql += " AND r.total_amount >= :amount_min"
                params["amount_min"] = amount_min

            if amount_max is not None:
                sql += " AND r.total_amount <= :amount_max"
                params["amount_max"] = amount_max

            # Order by relevance (BM25 score, lower is better)
            sql += " ORDER BY score ASC LIMIT :limit OFFSET :offset"

            result = await self._session.execute(text(sql), params)
            rows = result.fetchall()

            # Convert to SearchResult objects
            results = []
            for row in rows:
                # Generate snippet
                snippet = self._generate_snippet(
                    query, row.ocr_text or "", row.ai_comment or ""
                )

                results.append(
                    SearchResult(
                        receipt_id=row.receipt_id,
                        score=1.0 / (1.0 + row.score) if row.score else 0.0,
                        store_name=row.store_name,
                        total_amount=row.total_amount,
                        receipt_date=row.receipt_date,
                        category=row.category_name,
                        tags=row.tags.split(",") if row.tags else [],
                        snippet=snippet,
                    )
                )

            logger.info(
                "Search completed",
                extra={
                    "query": query,
                    "results_count": len(results),
                    "limit": limit,
                    "offset": offset,
                },
            )

            return results

        except Exception as e:
            logger.exception("Search failed", extra={"query": query, "error": str(e)})
            return []

    def _build_fts_query(self, query: str) -> str:
        """Build FTS5 query from user input.

        Args:
            query: User search query.

        Returns:
            FTS5 compatible query string.
        """
        # Sanitize query for FTS5
        # Split into terms and wrap each in quotes for phrase matching
        # Also support prefix matching with *
        terms = query.strip().split()
        if not terms:
            return '""'

        # Escape special characters
        escaped_terms = []
        for term in terms:
            # Remove FTS5 special chars except * for prefix
            term = term.replace('"', "").replace("'", "")
            if not term.endswith("*"):
                term = f'"{term}"'  # Phrase match
            escaped_terms.append(term)

        return " ".join(escaped_terms)

    def _generate_snippet(
        self, query: str, ocr_text: str, ai_comment: str
    ) -> str:
        """Generate text snippet highlighting search terms.

        Args:
            query: Search query.
            ocr_text: OCR text.
            ai_comment: AI comment.

        Returns:
            Snippet with context around matches.
        """
        # Combine texts
        combined = " ".join(filter(None, [ocr_text, ai_comment]))
        if not combined:
            return ""

        # Simple snippet: find first match and return surrounding context
        query_terms = query.lower().split()
        combined_lower = combined.lower()

        best_pos = -1
        for term in query_terms:
            pos = combined_lower.find(term)
            if pos >= 0:
                best_pos = pos
                break

        if best_pos < 0:
            # No match found, return beginning
            return combined[:200] + ("..." if len(combined) > 200 else "")

        # Return context around match
        start = max(0, best_pos - 50)
        end = min(len(combined), best_pos + 150)
        snippet = combined[start:end]

        if start > 0:
            snippet = "..." + snippet
        if end < len(combined):
            snippet = snippet + "..."

        return snippet

    async def rebuild_index(self) -> int:
        """Rebuild entire search index from receipts table.

        Useful for initial setup or after schema changes.

        Returns:
            Number of receipts indexed.
        """
        await self.initialize()

        try:
            # Clear existing index
            await self._session.execute(text(f"DELETE FROM {self.FTS_TABLE_NAME}"))

            # Get all receipts to index with tags and category in single query
            result = await self._session.execute(
                text(
                    """
                    SELECT
                        r.id, r.store_name, r.ocr_text, r.ai_comment,
                        r.category_id,
                        c.name as category_name,
                        group_concat(t.name, ',') as tags
                    FROM receipts r
                    LEFT JOIN categories c ON c.id = r.category_id
                    LEFT JOIN receipt_tags rt ON rt.receipt_id = r.id
                    LEFT JOIN tags t ON t.id = rt.tag_id
                    WHERE r.status IN ('approved', 'unapproved')
                    GROUP BY r.id
                    """
                )
            )
            rows = result.fetchall()

            # Batch insert
            for row in rows:
                tags_str = row.tags or ""
                category_name = row.category_name or ""

                await self._session.execute(
                    text(
                        f"""
                        INSERT INTO {self.FTS_TABLE_NAME}
                        (receipt_id, store_name, ocr_text, ai_comment, tags, category_name)
                        VALUES (:id, :store, :ocr, :ai, :tags, :cat)
                        """
                    ),
                    {
                        "id": row.id,
                        "store": row.store_name or "",
                        "ocr": row.ocr_text or "",
                        "ai": row.ai_comment or "",
                        "tags": tags_str,
                        "cat": category_name,
                    },
                )

            await self._session.commit()

            logger.info("Search index rebuilt", extra={"count": len(rows)})
            return len(rows)

        except Exception as e:
            logger.exception("Failed to rebuild index", extra={"error": str(e)})
            await self._session.rollback()
            return 0

    async def get_stats(self) -> SearchIndexStats:
        """Get search index statistics.

        Returns:
            SearchIndexStats with index information.
        """
        await self.initialize()

        try:
            # Count documents
            result = await self._session.execute(
                text(f"SELECT COUNT(*) FROM {self.FTS_TABLE_NAME}")
            )
            total_docs = result.scalar() or 0

            # Get index size (approximate)
            size_result = await self._session.execute(
                text("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
            )
            index_size = size_result.scalar() or 0

            return SearchIndexStats(
                total_documents=total_docs,
                last_updated=datetime.now(timezone.utc),  # Would need a metadata table for actual time
                index_size_bytes=index_size,
            )

        except Exception as e:
            logger.exception("Failed to get index stats", extra={"error": str(e)})
            return SearchIndexStats(
                total_documents=0,
                last_updated=None,
                index_size_bytes=0,
            )
