"""File monitoring service for watching unparsed receipt folders.

Implements RULE-BE-009: File system monitoring implementation.
Implements RULE-ERR-007: Unsupported file formats should be skipped with WARNING logs.
Implements RULE-BE-015: Background task processing (async tasks).
Implements RULE-GEN-021: Single responsibility principle.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.api import ObservedWatch

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.write_queue import WriteQueueManager
from app.services.ocr_service import OCRService
from app.services.receipt_analyzer import ReceiptAnalyzer, ReceiptAnalyzerConfig

logger = get_logger(__name__)


class FileMonitorHandler(FileSystemEventHandler):
    """File system event handler for receipt monitoring."""

    def __init__(
        self,
        write_queue_manager: WriteQueueManager,
        analyzer_config: ReceiptAnalyzerConfig,
        ocr_service: OCRService,
    ):
        """Initialize file monitor handler.

        Args:
            write_queue_manager: Write queue manager for database operations.
            analyzer_config: Configuration for receipt analyzer.
            ocr_service: OCR service for text extraction.
        """
        self.write_queue_manager = write_queue_manager
        self.analyzer_config = analyzer_config
        self.ocr_service = ocr_service
        
        # Supported image extensions (from settings)
        self.supported_extensions = [
            ext.lower() for ext in get_settings().supported_image_extensions
        ]

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events.

        Args:
            event: File system event.
        """
        if not event.is_directory:
            self._handle_file_creation(event.src_path)

    def _handle_file_creation(self, file_path: str) -> None:
        """Handle newly created file.

        Args:
            file_path: Path to the created file.
        """
        path = Path(file_path)
        
        # Check if file extension is supported
        if path.suffix.lower() not in self.supported_extensions:
            logger.warning(
                "Unsupported file format detected, skipping",
                extra={
                    "file_path": str(path),
                    "extension": path.suffix,
                },
            )
            return

        # Process the file asynchronously
        try:
            asyncio.create_task(self._process_file(path))
        except Exception as e:
            logger.error(
                "Failed to create async task for file processing",
                extra={
                    "file_path": str(path),
                    "error": str(e),
                },
            )

    async def _process_file(self, file_path: Path) -> None:
        """Process a newly detected file.

        Args:
            file_path: Path to the file to process.
        """
        logger.info("Processing new receipt file", extra={"file_path": str(file_path)})
        
        try:
            # Create analyzer instance
            analyzer = ReceiptAnalyzer(
                config=self.analyzer_config,
                write_queue_manager=self.write_queue_manager,
                ocr_service=self.ocr_service,
            )
            
            # Process the file asynchronously
            await analyzer.process_receipt_file(file_path)
            
            logger.info("File processing completed successfully", extra={"file_path": str(file_path)})
        except Exception as e:
            logger.error(
                "Failed to process receipt file",
                extra={
                    "file_path": str(file_path),
                    "error": str(e),
                },
            )


class FileMonitorService:
    """File monitoring service for watching unparsed receipt folders.

    Implements RULE-BE-009: File system monitoring implementation.
    Implements RULE-BE-015: Background task processing (async tasks).
    Implements RULE-GEN-021: Single responsibility principle.
    """

    def __init__(self) -> None:
        """Initialize file monitor service."""
        self._observer: Optional[Observer] = None
        self._watch: Optional[ObservedWatch] = None
        self._is_running = False
        self._settings = get_settings()
        
        # Get the unparsed directory from settings
        self.unparsed_dir = self._settings.unparsed_dir
        
        logger.info(
            "File monitor service initialized",
            extra={
                "unparsed_dir": str(self.unparsed_dir),
                "supported_extensions": self._settings.supported_image_extensions,
            },
        )

    async def start(self, write_queue_manager: WriteQueueManager) -> None:
        """Start file monitoring.

        Args:
            write_queue_manager: Write queue manager for database operations.
        """
        if self._is_running:
            logger.warning("File monitor service already running")
            return

        # Create observer
        self._observer = Observer()
        
        # Create handler
        analyzer_config = ReceiptAnalyzerConfig.from_settings()
        ocr_service = OCRService()
        handler = FileMonitorHandler(
            write_queue_manager=write_queue_manager,
            analyzer_config=analyzer_config,
            ocr_service=ocr_service,
        )
        
        # Watch the unparsed directory
        self._watch = self._observer.schedule(
            handler,
            str(self.unparsed_dir),
            recursive=self._settings.watchdog_recursive,
        )
        
        # Start observer
        self._observer.start()
        self._is_running = True
        
        logger.info(
            "File monitor service started",
            extra={
                "unparsed_dir": str(self.unparsed_dir),
                "recursive": self._settings.watchdog_recursive,
            },
        )

    async def stop(self, timeout: float = 5.0) -> None:
        """Stop file monitoring gracefully.

        Args:
            timeout: Timeout in seconds for graceful shutdown.
        """
        if not self._is_running:
            logger.warning("File monitor service not running")
            return

        logger.info("Stopping file monitor service...")
        
        # Stop observer
        if self._observer:
            self._observer.stop()
            
        # Wait for observer to stop
        try:
            await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, self._observer.join),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning("File monitor service stop timed out")
        except Exception as e:
            logger.error(
                "Error during file monitor service shutdown",
                extra={"error": str(e)},
            )

        self._is_running = False
        logger.info("File monitor service stopped")

    @property
    def is_running(self) -> bool:
        """Check if service is running."""
        return self._is_running

    async def restart(self, write_queue_manager: WriteQueueManager) -> None:
        """Restart file monitoring.

        Args:
            write_queue_manager: Write queue manager for database operations.
        """
        await self.stop()
        await self.start(write_queue_manager)