"""Application constants and enumerations."""

from enum import StrEnum


class AppEnvironment(StrEnum):
    """Application environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    """Log levels (RULE-ERR-013)."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(StrEnum):
    """Log output formats."""

    JSON = "json"
    TEXT = "text"


class ReceiptStatus(StrEnum):
    """Receipt processing status."""

    UNPARSED = "unparsed"  # 未解析フォルダにある状態
    PARSING = "parsing"  # 解析中
    UNPARSED_FAILED = "unparsed_failed"  # 解析失敗 → 失敗フォルダ
    UNAPPROVED = "unapproved"  # 未承認フォルダ（重複候補あり等）
    APPROVED = "approved"  # 承認済み・承認フォルダ
    REJECTED = "rejected"  # 却下
    FAILED = "failed"  # 処理失敗（失敗フォルダ）


class AccountCategory(StrEnum):
    """勘定科目（勘定科目判定で使用）."""

    TRAVEL_EXPENSE = "旅費交通費"
    ENTERTAINMENT = "交際費"
    SUPPLIES = "消耗品費"
    COMMUNICATION = "通信費"
    UTILITIES = "水道光熱費"
    RENT = "地代家賃"
    SALARY = "給与賃金"
    OUTSOURCING = "外注費"
    ADVERTISING = "広告宣伝費"
    REPAIR = "修繕費"
    INSURANCE = "保険料"
    TAXES = "租税公課"
    DEPRECIATION = "減価償却費"
    OTHER = "その他"


class FileExtension(StrEnum):
    """Supported image file extensions."""

    JPG = ".jpg"
    JPEG = ".jpeg"
    PNG = ".png"
    WEBP = ".webp"
    TIFF = ".tiff"
    BMP = ".bmp"


# API
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Health check
HEALTH_CHECK_PATH = "/health"

# File naming pattern for approved receipts (RULE-FLOW-001-11)
# Format: {date}_{store}_{amount}_{category}_{tags}_{hash}.{ext}
APPROVED_FILENAME_PATTERN = "{date}_{store}_{amount}_{category}_{tags}_{hash}.{ext}"
DATE_FORMAT = "%Y%m%d"
DATETIME_FORMAT = "%Y%m%d_%H%M%S"

# Error messages
ERROR_MESSAGES = {
    "FILE_NOT_FOUND": "ファイルが見つかりません",
    "FILE_TOO_LARGE": "ファイルサイズが上限を超えています",
    "UNSUPPORTED_FORMAT": "サポートされていないファイル形式です",
    "OCR_FAILED": "OCR処理に失敗しました",
    "AI_ANALYSIS_FAILED": "AI解析に失敗しました",
    "DATABASE_ERROR": "データベースエラーが発生しました",
    "DUPLICATE_DETECTED": "重複候補が検出されました",
    "VALIDATION_ERROR": "バリデーションエラー",
    "NOT_FOUND": "リソースが見つかりません",
    "INTERNAL_ERROR": "内部エラーが発生しました",
}

# Success messages
SUCCESS_MESSAGES = {
    "FILE_MOVED": "ファイルを移動しました",
    "RECEIPT_PARSED": "レシートを解析しました",
    "RECEIPT_APPROVED": "レシートを承認しました",
    "RECEIPT_REJECTED": "レシートを却下しました",
    "HEALTH_OK": "システム正常",
}
