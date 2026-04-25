# BACKEND ENGINEER RUNBOOK
## Cards-4-Sale: Phase 1-3 Implementation Guide

**Target Role:** Senior Backend Engineer  
**Phases Assigned:** 1, 2 (partial), 3  
**Timeline:** Weeks 1-3  
**Success Criteria:** All critical fixes complete, services extracted, caching implemented

---

## YOUR MISSION

You are responsible for:
1. **Week 1:** Logging, error handling, database safety
2. **Week 2:** Extract business logic into services, DI container
3. **Week 3:** Implement caching, rate limiting, performance optimization

By end of Week 3, the backend should be **production-grade, testable, and performant**.

---

## WEEK 1: CRITICAL FIXES

### Task 1.1: Implement Logging System (2-3 hours)

**Objective:** Replace all `print()` statements with structured logging.

**Deliverable:** `src/logging_config.py`

```python
"""
Logging configuration for Cards-4-Sale.
Provides structured logging with file rotation and multiple handlers.
"""
import logging
import logging.handlers
import os
from pathlib import Path

# Create logs directory
LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)

# Determine log level from environment
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

def configure_logging():
    """Configure logging for the application."""
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (always INFO or higher)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel('INFO')
    
    # File handler (rotating, 10MB per file, keep 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / 'app.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(LOG_LEVEL)
    
    # Error file handler (ERROR and CRITICAL only)
    error_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / 'errors.log',
        maxBytes=5 * 1024 * 1024,
        backupCount=10
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel('ERROR')
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel('WARNING')
    logging.getLogger('requests').setLevel('WARNING')
    logging.getLogger('werkzeug').setLevel('WARNING')


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module."""
    return logging.getLogger(name)
```

**Usage in all modules:**
```python
# At the top of each file:
from src.logging_config import get_logger

logger = get_logger(__name__)

# Replace all print() with:
logger.info("Starting image analysis...")
logger.warning("Fallback to mock data - API unavailable")
logger.error("Database connection failed", exc_info=True)
logger.debug("Processing listing with threshold: 20.0")
```

**Action Items:**
- [ ] Create `src/logging_config.py` with code above
- [ ] Update `src/app.py` - add to `create_app()`: `from src.logging_config import configure_logging; configure_logging()`
- [ ] Replace all `print()` in:
  - `src/api/openai_client.py` (4 replacements)
  - `src/api/ebay_client.py` (2 replacements)
  - `src/app.py` (8 replacements)
  - `src/database.py` (6 replacements)
  - `src/main.py` (10 replacements)
- [ ] Create `.gitignore` entry: `logs/`
- [ ] Test: Run app, verify `logs/app.log` is created

**Validation:**
```bash
python -m src.app
# Should see console output AND logs/app.log created with same messages
tail logs/app.log
# Should show timestamped entries
```

---

### Task 1.2: Create Exception Hierarchy (1-2 hours)

**Objective:** Replace generic exceptions with domain-specific ones.

**Deliverable:** `src/exceptions.py`

```python
"""
Custom exceptions for Cards-4-Sale.
Provides semantic error handling with context.
"""


class CardsForSaleException(Exception):
    """Base exception for all Cards-4-Sale errors."""
    pass


class ImageAnalysisError(CardsForSaleException):
    """Raised when image analysis fails."""
    
    def __init__(self, image_path: str, reason: str, original_error: Exception = None):
        self.image_path = image_path
        self.reason = reason
        self.original_error = original_error
        super().__init__(
            f"Image analysis failed for {image_path}: {reason}"
        )


class EbayAPIError(CardsForSaleException):
    """Raised when eBay API call fails."""
    
    def __init__(self, operation: str, query: str = None, reason: str = None):
        self.operation = operation
        self.query = query
        self.reason = reason
        msg = f"eBay {operation} failed"
        if query:
            msg += f" for '{query}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class OpenAIAPIError(CardsForSaleException):
    """Raised when OpenAI API call fails."""
    
    def __init__(self, operation: str, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(f"OpenAI {operation} failed: {reason}")


class DatabaseError(CardsForSaleException):
    """Raised when database operation fails."""
    
    def __init__(self, operation: str, reason: str, original_error: Exception = None):
        self.operation = operation
        self.reason = reason
        self.original_error = original_error
        super().__init__(f"Database {operation} failed: {reason}")


class ListingGenerationError(CardsForSaleException):
    """Raised when listing generation fails."""
    
    def __init__(self, stage: str, reason: str, original_error: Exception = None):
        self.stage = stage
        self.reason = reason
        self.original_error = original_error
        super().__init__(f"Listing generation failed at {stage}: {reason}")


class ValidationError(CardsForSaleException):
    """Raised when input validation fails."""
    
    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"Validation failed for {field}: {reason}")
```

**Usage:**
```python
# Before:
try:
    result = describe_image(path)
except Exception as e:
    print(f"Error: {e}")
    return describe_image_mock(path)

# After:
from src.exceptions import ImageAnalysisError
from src.logging_config import get_logger

logger = get_logger(__name__)

try:
    result = describe_image(path)
except FileNotFoundError as e:
    raise ImageAnalysisError(path, "File not found", original_error=e)
except Exception as e:
    logger.warning(f"Image analysis failed: {e}. Using mock.")
    raise ImageAnalysisError(path, f"API error: {str(e)}", original_error=e)
```

**Action Items:**
- [ ] Create `src/exceptions.py` with code above
- [ ] Update `src/api/openai_client.py`:
  - Add imports at top
  - Wrap API calls with try/except
  - Raise `ImageAnalysisError` on failure
  - Still fall back to mock for UX
- [ ] Update `src/api/ebay_client.py`:
  - Raise `EbayAPIError` on API failure
  - Include query context in error
- [ ] Update `src/app.py`:
  - Import exceptions
  - Catch specific exceptions in routes
  - Return appropriate HTTP status codes

---

### Task 1.3: Database Transaction Safety (3-4 hours)

**Objective:** Add transaction management and rollback capability.

**Deliverable:** Refactored `src/database.py`

```python
"""
Database operations with transaction safety.
All writes are atomic - either fully succeed or fully rollback.
"""

import sqlite3
import json
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

DATABASE_PATH = Path(__file__).parent.parent / "listings.db"


@contextmanager
def get_db_connection(timeout: int = 30):
    """
    Context manager for safe database connections.
    Handles commit/rollback automatically.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
    """
    conn = sqlite3.connect(DATABASE_PATH, timeout=timeout)
    conn.row_factory = sqlite3.Row  # Better row access
    conn.execute("PRAGMA foreign_keys = ON")  # Enable FK constraints
    
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.exception(f"Database transaction failed: {e}")
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database with proper schema and indexes."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create listings table
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                filename TEXT,
                category TEXT,
                condition TEXT,
                brand TEXT,
                model TEXT,
                features TEXT,
                suggested_price REAL,
                comparable_listings TEXT,
                payload TEXT NOT NULL,
                status TEXT DEFAULT 'draft',
                external_listing_id TEXT UNIQUE,
                published_at TIMESTAMP,
                publish_error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        
        # Add missing columns for existing databases
        cursor.execute("PRAGMA table_info(listings)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        columns_to_add = {
            'external_listing_id': 'ALTER TABLE listings ADD COLUMN external_listing_id TEXT UNIQUE',
            'published_at': 'ALTER TABLE listings ADD COLUMN published_at TIMESTAMP',
            'publish_error': 'ALTER TABLE listings ADD COLUMN publish_error TEXT',
        }
        
        for col_name, alter_sql in columns_to_add.items():
            if col_name not in existing_columns:
                cursor.execute(alter_sql)
        
        # Create indexes for query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON listings(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON listings(created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_external_listing_id ON listings(external_listing_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_brand_model ON listings(brand, model)")
        
        logger.info("Database initialized successfully")


def save_listing(
    title: str,
    filename: str,
    analysis: dict,
    comparable_listings: list,
    suggested_price: float,
    payload: dict
) -> Optional[int]:
    """
    Save a listing to database with atomic transaction.
    
    Returns:
        Listing ID if successful, None if failed
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                INSERT INTO listings
                (title, filename, category, condition, brand, model, features,
                 suggested_price, comparable_listings, payload, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    title,
                    filename,
                    analysis.get("category", ""),
                    analysis.get("condition", ""),
                    analysis.get("brand", ""),
                    analysis.get("model", ""),
                    json.dumps(analysis.get("features", [])),
                    suggested_price,
                    json.dumps(comparable_listings),
                    json.dumps(payload),
                    "draft",
                ),
            )
            
            listing_id = cursor.lastrowid
            logger.info(f"Saved listing {listing_id}: {title}")
            return listing_id
            
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity constraint violation: {e}")
        return None
    except Exception as e:
        logger.exception(f"Failed to save listing: {e}")
        return None


def get_all_listings() -> List[Dict[str, Any]]:
    """Get all listings from database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                SELECT id, title, filename, category, condition, brand, model,
                       suggested_price, status, created_at, updated_at
                FROM listings
                ORDER BY created_at DESC, id DESC
                '''
            )
            
            listings = []
            for row in cursor.fetchall():
                listings.append({
                    "id": row[0],
                    "title": row[1],
                    "filename": row[2],
                    "category": row[3],
                    "condition": row[4],
                    "brand": row[5],
                    "model": row[6],
                    "suggested_price": row[7],
                    "status": row[8],
                    "created_at": row[9],
                    "updated_at": row[10],
                })
            
            return listings
            
    except Exception as e:
        logger.exception(f"Failed to fetch listings: {e}")
        return []


def get_listing(listing_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific listing by ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                SELECT id, title, filename, category, condition, brand, model, features,
                       suggested_price, comparable_listings, payload, status, external_listing_id,
                       published_at, publish_error, created_at, updated_at
                FROM listings
                WHERE id = ?
                ''',
                (listing_id,),
            )
            
            row = cursor.fetchone()
        
        if not row:
            return None
        
        # Safely parse JSON fields
        features = _safe_json_parse(row[7], default=[])
        comparable_listings = _safe_json_parse(row[9], default=[])
        payload = _safe_json_parse(row[10], default={})
        
        return {
            "id": row[0],
            "title": row[1],
            "filename": row[2],
            "category": row[3],
            "condition": row[4],
            "brand": row[5],
            "model": row[6],
            "features": features,
            "suggested_price": row[8],
            "comparable_listings": comparable_listings,
            "payload": payload,
            "status": row[11],
            "external_listing_id": row[12],
            "published_at": row[13],
            "publish_error": row[14],
            "created_at": row[15],
            "updated_at": row[16],
        }
        
    except Exception as e:
        logger.exception(f"Failed to fetch listing {listing_id}: {e}")
        return None


def update_listing_status(listing_id: int, status: str) -> bool:
    """Update listing status (draft, published, archived)."""
    valid_statuses = {'draft', 'published', 'archived'}
    if status not in valid_statuses:
        logger.warning(f"Invalid status: {status}")
        return False
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                UPDATE listings
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''',
                (status, listing_id),
            )
            
            updated = cursor.rowcount
            if updated > 0:
                logger.info(f"Updated listing {listing_id} status to {status}")
            return updated > 0
            
    except Exception as e:
        logger.exception(f"Failed to update listing status: {e}")
        return False


def delete_listing(listing_id: int) -> bool:
    """Delete a listing from database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM listings WHERE id = ?", (listing_id,))
            
            deleted = cursor.rowcount
            if deleted > 0:
                logger.info(f"Deleted listing {listing_id}")
            return deleted > 0
            
    except Exception as e:
        logger.exception(f"Failed to delete listing: {e}")
        return False


def record_publish_result(
    listing_id: int,
    published: bool,
    external_listing_id: Optional[str] = None,
    error_message: Optional[str] = None
) -> bool:
    """Record publish success/failure metadata for a listing."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if published:
                cursor.execute(
                    '''
                    UPDATE listings
                    SET status = 'published',
                        external_listing_id = ?,
                        published_at = CURRENT_TIMESTAMP,
                        publish_error = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    ''',
                    (external_listing_id, listing_id),
                )
                logger.info(f"Marked listing {listing_id} as published: {external_listing_id}")
            else:
                cursor.execute(
                    '''
                    UPDATE listings
                    SET publish_error = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    ''',
                    (error_message, listing_id),
                )
                logger.warning(f"Publish failed for listing {listing_id}: {error_message}")
            
            updated = cursor.rowcount
            return updated > 0
            
    except Exception as e:
        logger.exception(f"Failed to record publish result: {e}")
        return False


def get_stats() -> Dict[str, int]:
    """Get database statistics."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            queries = [
                ("SELECT COUNT(*) FROM listings", "total"),
                ("SELECT COUNT(*) FROM listings WHERE status = 'draft'", "drafts"),
                ("SELECT COUNT(*) FROM listings WHERE status = 'published'", "published"),
                ("SELECT COUNT(*) FROM listings WHERE status = 'archived'", "archived"),
            ]
            
            stats = {}
            for query, key in queries:
                cursor.execute(query)
                stats[key] = cursor.fetchone()[0]
            
            return stats
            
    except Exception as e:
        logger.exception(f"Failed to get stats: {e}")
        return {"total": 0, "drafts": 0, "published": 0, "archived": 0}


def _safe_json_parse(data: Optional[str], default: Any = None) -> Any:
    """Parse JSON string safely with logging on failure."""
    if not data:
        return default if default is not None else []
    
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error: {e}. Data preview: {data[:100]}")
        return default if default is not None else []
```

**Action Items:**
- [ ] Backup current `src/database.py`
- [ ] Replace with new version above
- [ ] Update all database calls in `src/app.py` to handle exceptions
- [ ] Test transaction safety:
  ```bash
  pytest tests/test_database.py -v
  ```
- [ ] Verify database initialization:
  ```bash
  python -c "from src.database import init_db; init_db()"
  sqlite3 listings.db ".schema"  # Should show indexes
  ```

---

### Task 1.4: Input Validation Layer (2-3 hours)

**Objective:** Create comprehensive input validation before processing.

**Deliverable:** `src/validators.py`

```python
"""
Input validation for uploaded files and API payloads.
Validates early to prevent bad data from entering the system.
"""

import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class ImageValidator:
    """Validates uploaded image files."""
    
    ALLOWED_TYPES = {'jpg', 'jpeg', 'png', 'gif'}
    MAX_SIZE_BYTES = 16 * 1024 * 1024  # 16MB
    MAX_FILENAME_LENGTH = 256
    FORBIDDEN_CHARS = {'\x00', '/', '\\'}
    
    @staticmethod
    def validate_upload(filename: str, file_size: int) -> Tuple[bool, str]:
        """
        Validate uploaded file metadata.
        
        Returns:
            (is_valid, error_message)
        """
        # Check filename exists and length
        if not filename:
            return False, "Filename is empty"
        
        if len(filename) > ImageValidator.MAX_FILENAME_LENGTH:
            return False, f"Filename too long (max {ImageValidator.MAX_FILENAME_LENGTH} chars)"
        
        # Check for forbidden characters
        if any(char in filename for char in ImageValidator.FORBIDDEN_CHARS):
            return False, "Filename contains forbidden characters"
        
        # Check file type
        try:
            ext = filename.rsplit('.', 1)[1].lower()
        except IndexError:
            return False, "Filename has no extension"
        
        if ext not in ImageValidator.ALLOWED_TYPES:
            return False, f"Unsupported file type: {ext}. Allowed: {', '.join(ImageValidator.ALLOWED_TYPES)}"
        
        # Check file size
        if file_size == 0:
            return False, "File is empty"
        
        if file_size > ImageValidator.MAX_SIZE_BYTES:
            size_mb = file_size / 1024 / 1024
            return False, f"File too large: {size_mb:.1f}MB (max 16MB)"
        
        return True, ""
    
    @staticmethod
    def validate_mime_type(mime_type: str) -> bool:
        """Validate MIME type matches extension."""
        allowed_mimes = {
            'image/jpeg': {'jpg', 'jpeg'},
            'image/png': {'png'},
            'image/gif': {'gif'},
        }
        return mime_type in allowed_mimes


class ListingValidator:
    """Validates generated eBay listing payloads."""
    
    MIN_PRICE = 0.99
    MAX_PRICE = 100000.00
    MAX_TITLE_LENGTH = 80
    MAX_DESCRIPTION_LENGTH = 5000
    
    @staticmethod
    def validate_payload(payload: dict) -> Tuple[bool, str]:
        """
        Validate eBay listing payload before saving.
        
        Returns:
            (is_valid, error_message)
        """
        if not isinstance(payload, dict):
            return False, "Payload must be a dictionary"
        
        # Check required fields
        if 'sku' not in payload:
            return False, "Missing SKU"
        
        if 'product' not in payload or not isinstance(payload['product'], dict):
            return False, "Missing or invalid product section"
        
        # Validate title
        title = payload.get('product', {}).get('title', '').strip()
        if not title:
            return False, "Title is required"
        
        if len(title) > ListingValidator.MAX_TITLE_LENGTH:
            return False, f"Title too long (max {ListingValidator.MAX_TITLE_LENGTH} chars, got {len(title)})"
        
        # Validate description
        description = payload.get('product', {}).get('description', '').strip()
        if description and len(description) > ListingValidator.MAX_DESCRIPTION_LENGTH:
            return False, f"Description too long (max {ListingValidator.MAX_DESCRIPTION_LENGTH} chars)"
        
        # Validate price
        try:
            price_data = payload.get('price', {})
            if not price_data:
                return False, "Missing price"
            
            price_value = price_data.get('value')
            if price_value is None:
                return False, "Missing price value"
            
            price_float = float(price_value)
            
            if not (ListingValidator.MIN_PRICE <= price_float <= ListingValidator.MAX_PRICE):
                return False, f"Price {price_float} out of range (${ListingValidator.MIN_PRICE} - ${ListingValidator.MAX_PRICE})"
            
            currency = price_data.get('currency', 'USD')
            if currency != 'USD':
                return False, f"Only USD currency supported (got {currency})"
                
        except (ValueError, TypeError) as e:
            return False, f"Invalid price format: {e}"
        
        # Validate condition
        valid_conditions = {
            'NEW', 'REFURBISHED', 'USED_LIKE_NEW', 'USED_GOOD',
            'USED_ACCEPTABLE', 'NOT_SPECIFIED'
        }
        condition = payload.get('condition', 'USED_GOOD')
        if condition not in valid_conditions:
            return False, f"Invalid condition: {condition}"
        
        return True, ""


class AnalysisValidator:
    """Validates image analysis results from OpenAI."""
    
    REQUIRED_FIELDS = {'brand', 'model', 'category', 'condition'}
    
    @staticmethod
    def validate_analysis(analysis: dict) -> Tuple[bool, str]:
        """Validate image analysis structure."""
        if not isinstance(analysis, dict):
            return False, "Analysis must be a dictionary"
        
        # Check for multi-card structure
        if 'cards' in analysis:
            if not isinstance(analysis['cards'], list):
                return False, "Cards must be a list"
            if not analysis['cards']:
                return False, "Cards list is empty"
            
            # Validate each card
            for i, card in enumerate(analysis['cards']):
                is_valid, error = AnalysisValidator._validate_single(card)
                if not is_valid:
                    return False, f"Card {i}: {error}"
        else:
            # Single item
            is_valid, error = AnalysisValidator._validate_single(analysis)
            if not is_valid:
                return False, error
        
        return True, ""
    
    @staticmethod
    def _validate_single(item: dict) -> Tuple[bool, str]:
        """Validate a single item/card."""
        # Check required fields
        for field in AnalysisValidator.REQUIRED_FIELDS:
            if field not in item:
                return False, f"Missing required field: {field}"
            
            value = item[field]
            if not isinstance(value, str) or not value.strip():
                return False, f"Field '{field}' is empty or not a string"
        
        # Check features if present
        if 'features' in item:
            features = item['features']
            if features and not isinstance(features, (list, str)):
                return False, "Features must be a list or string"
        
        # Check price range if present
        if 'estimated_value_range' in item:
            value = item['estimated_value_range']
            if value and not isinstance(value, str):
                return False, "Estimated value must be a string"
        
        return True, ""
```

**Usage in app.py:**
```python
from src.validators import ImageValidator, ListingValidator, AnalysisValidator
from src.exceptions import ValidationError

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        # Validate file
        is_valid, error = ImageValidator.validate_upload(file.filename, file.size)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        # ... rest of processing ...
        
        # Validate analysis before saving
        is_valid, error = AnalysisValidator.validate_analysis(analysis)
        if not is_valid:
            logger.warning(f"Invalid analysis: {error}")
            return jsonify({'error': 'Analysis validation failed'}), 400
        
        # Validate payload before publishing
        is_valid, error = ListingValidator.validate_payload(payload)
        if not is_valid:
            logger.warning(f"Invalid payload: {error}")
            return jsonify({'error': 'Payload validation failed'}), 400
        
        return jsonify({'success': True}), 200
        
    except ValidationError as e:
        return jsonify({'error': f"Validation error: {e}"}), 400
```

**Action Items:**
- [ ] Create `src/validators.py` with code above
- [ ] Update `src/app.py` to use validators in all routes
- [ ] Add validation tests:
  ```bash
  pytest tests/test_validators.py -v
  ```

---

### Task 1.5: Configuration Validation (1 hour)

**Objective:** Fail fast on startup if config is invalid.

**Update:** `src/config.py` - Add at end:

```python
def validate_config():
    """Validate configuration on startup."""
    errors = []
    
    # Check real API mode requirements
    if not USE_OPENAI_MOCK and not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY required when USE_OPENAI_MOCK=False")
    
    if not USE_EBAY_MOCK and not (EBAY_CLIENT_ID and EBAY_CLIENT_SECRET):
        errors.append("eBay credentials (EBAY_CLIENT_ID, EBAY_CLIENT_SECRET) required when USE_EBAY_MOCK=False")
    
    if errors:
        error_msg = "\n".join(f"  - {e}" for e in errors)
        raise ValueError(f"Configuration validation failed:\n{error_msg}")
    
    return True
```

**In app.py:**
```python
from src.config import validate_config

def create_app():
    # Validate config first
    validate_config()
    
    app = Flask(...)
    # ... rest of app setup ...
```

**Action Items:**
- [ ] Add validation function to `src/config.py`
- [ ] Call in `create_app()` before any API setup
- [ ] Test: Try running with missing eBay credentials
  ```bash
  USE_EBAY_MOCK=False python -m src.app
  # Should raise ValueError immediately
  ```

---

## WEEK 1 SUMMARY

**Deliverables:**
- ✅ `src/logging_config.py` - Structured logging
- ✅ `src/exceptions.py` - Custom exceptions
- ✅ Refactored `src/database.py` - Transaction safety
- ✅ `src/validators.py` - Input validation
- ✅ Updated `src/config.py` - Startup validation

**Verification:**
```bash
# Run all tests
pytest tests/ -v --tb=short

# Check logs are created
python -m src.app
tail logs/app.log

# Verify database safety
python -m pytest tests/test_database.py -v
```

**By end of Week 1:**
- All critical bugs fixed
- Proper error handling throughout
- No more `print()` statements
- Database transactions are safe
- Invalid input rejected early

---

## WEEK 2: EXTRACT SERVICES & DI CONTAINER

### Task 2.1: Create Services Layer (6-8 hours)

**Objective:** Extract business logic from Flask routes into testable services.

**Deliverable:** `src/services/listing_service.py`

[See IMPLEMENTATION SECTION 3.1 in main review for full code]

Key Points:
- `ListingService` orchestrates image analysis → eBay search → price calculation → listing creation
- Testable (can inject mock APIs)
- Reusable (can call from CLI or other routes)
- Clear error handling with custom exceptions

**Action Items:**
- [ ] Create `src/services/__init__.py` (empty)
- [ ] Create `src/services/listing_service.py` with full implementation
- [ ] Create unit tests: `tests/test_listing_service.py`
- [ ] Refactor `src/app.py` to use ListingService instead of direct function calls
- [ ] Update tests to verify service behavior

---

### Task 2.2: Create Title Builder Service (2-3 hours)

**Objective:** Extract title building logic into reusable, testable service.

**Deliverable:** `src/services/title_builder.py`

```python
"""
Builds SEO-optimized eBay listing titles.
Handles both generic items and trading cards.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class TitleBuilder:
    """Builds eBay listing titles with optimization for search."""
    
    DEFAULT_MAX_LENGTH = 80
    
    def __init__(self, max_length: int = DEFAULT_MAX_LENGTH):
        self.max_length = max_length
    
    def build(self, analysis: Dict[str, any]) -> str:
        """
        Build title from analysis.
        
        For trading cards, prioritizes player name for searchability.
        For generic items, uses brand + model.
        """
        if not analysis:
            return "Item"
        
        if self._is_trading_card(analysis):
            return self._build_card_title(analysis)
        
        return self._build_generic_title(analysis)
    
    def _is_trading_card(self, analysis: Dict) -> bool:
        """Check if item is a trading card."""
        category = analysis.get('category', '').lower()
        return 'card' in category
    
    def _build_card_title(self, analysis: Dict) -> str:
        """
        Build title for trading card.
        
        Order of priority:
        1. Player name (most searchable)
        2. Set name
        3. Year
        4. Brand
        5. Model
        """
        parts = []
        
        # Player name is most important for card searchability
        if analysis.get('player_name'):
            parts.append(analysis['player_name'])
        
        # Brand (usually card manufacturer)
        if analysis.get('brand'):
            parts.append(analysis['brand'])
        
        # Card details in model
        if analysis.get('model'):
            parts.append(analysis['model'])
        
        # Year can help distinguish between years
        if analysis.get('year') and 'year' not in str(parts).lower():
            parts.append(f"({analysis['year']})")
        
        title = ' '.join(str(p) for p in parts if p).strip()
        
        # Trim to max length on word boundary
        if len(title) > self.max_length:
            title = title[:self.max_length].rsplit(' ', 1)[0].strip()
        
        logger.debug(f"Built card title: {title}")
        return title
    
    def _build_generic_title(self, analysis: Dict) -> str:
        """
        Build title for generic item.
        
        Standard format: Brand Model Variant
        """
        parts = []
        
        if analysis.get('brand'):
            parts.append(analysis['brand'])
        
        if analysis.get('model'):
            parts.append(analysis['model'])
        
        title = ' '.join(str(p) for p in parts if p).strip()
        
        if not title:
            title = analysis.get('category', 'Item')
        
        # Trim to max length
        if len(title) > self.max_length:
            title = title[:self.max_length].rsplit(' ', 1)[0].strip()
        
        logger.debug(f"Built generic title: {title}")
        return title
```

**Action Items:**
- [ ] Create `src/services/title_builder.py`
- [ ] Create tests: `tests/test_title_builder.py`
  ```python
  def test_builds_card_title_with_player_name():
      builder = TitleBuilder()
      analysis = {
          'category': 'Sports Trading Cards',
          'player_name': 'Shohei Ohtani',
          'brand': 'Topps',
          'model': 'Rookie Card',
          'year': '2018'
      }
      title = builder.build(analysis)
      assert 'Shohei Ohtani' in title
      assert len(title) <= 80
  
  def test_builds_generic_title():
      builder = TitleBuilder()
      analysis = {
          'brand': 'Sony',
          'model': 'WH-1000XM4 Headphones'
      }
      title = builder.build(analysis)
      assert 'Sony' in title
      assert len(title) <= 80
  ```

---

### Task 2.3: Create Description Builder Service (2-3 hours)

**Objective:** Extract description formatting into a service.

**Deliverable:** `src/services/description_builder.py`

```python
"""
Builds eBay-formatted listing descriptions.
Produces plain text (not markdown) for eBay compatibility.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class DescriptionBuilder:
    """Builds eBay listing descriptions with proper formatting."""
    
    MAX_LENGTH = 5000
    
    def build(self, analysis: Dict) -> str:
        """
        Build description from analysis.
        Returns plain-text formatted for eBay (no markdown).
        """
        lines = []
        
        # Header with item summary
        lines.append("=" * 50)
        lines.append(self._build_header(analysis))
        lines.append("=" * 50)
        lines.append("")
        
        # Basic attributes
        if analysis.get('category'):
            lines.append(f"CATEGORY: {analysis['category']}")
        
        if analysis.get('condition'):
            lines.append(f"CONDITION: {analysis['condition']}")
        
        if analysis.get('brand'):
            lines.append(f"BRAND: {analysis['brand']}")
        
        if analysis.get('model'):
            lines.append(f"MODEL: {analysis['model']}")
        
        lines.append("")
        
        # Features section
        if analysis.get('features'):
            lines.append("KEY FEATURES:")
            features = analysis['features']
            if isinstance(features, list):
                for feature in features:
                    lines.append(f"  • {feature}")
            else:
                lines.append(f"  • {features}")
            lines.append("")
        
        # Grading/Condition notes (for cards)
        if analysis.get('grading_notes'):
            lines.append("CONDITION DETAILS:")
            notes = analysis['grading_notes']
            if isinstance(notes, list):
                for note in notes:
                    lines.append(f"  • {note}")
            else:
                lines.append(f"  • {notes}")
            lines.append("")
        
        # Trading card specific fields
        if self._is_trading_card(analysis):
            lines.extend(self._build_card_details(analysis))
        
        # Footer
        lines.append("-" * 50)
        lines.append("Thanks for visiting! Questions? Feel free to ask.")
        
        description = '\n'.join(lines)
        
        # Trim to eBay limit
        if len(description) > self.MAX_LENGTH:
            description = description[:self.MAX_LENGTH-100] + "\n\n[Description truncated]"
        
        logger.debug(f"Built description ({len(description)} chars)")
        return description
    
    def _build_header(self, analysis: Dict) -> str:
        """Build header with item name."""
        parts = []
        if analysis.get('brand'):
            parts.append(analysis['brand'])
        if analysis.get('model'):
            parts.append(analysis['model'])
        if analysis.get('player_name'):
            parts.append(f"({analysis['player_name']})")
        return ' '.join(parts) if parts else 'Item'
    
    def _is_trading_card(self, analysis: Dict) -> bool:
        """Check if item is trading card."""
        return 'card' in analysis.get('category', '').lower()
    
    def _build_card_details(self, analysis: Dict) -> List[str]:
        """Build trading card specific details."""
        lines = []
        
        card_fields = [
            ('set_name', 'SET'),
            ('year', 'YEAR'),
            ('card_number', 'CARD #'),
            ('grade', 'GRADE'),
        ]
        
        has_card_info = False
        for key, label in card_fields:
            if analysis.get(key):
                lines.append(f"{label}: {analysis[key]}")
                has_card_info = True
        
        if has_card_info:
            lines.append("")
        
        return lines
```

**Action Items:**
- [ ] Create `src/services/description_builder.py`
- [ ] Create tests: `tests/test_description_builder.py`
- [ ] Verify descriptions don't contain markdown

---

### Task 2.4: Create DI Container (2 hours)

**Objective:** Centralize dependency injection for testability.

**Deliverable:** `src/container.py`

```python
"""
Dependency Injection Container.
Manages creation and wiring of service instances.
Allows easy swapping of real vs mock implementations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Protocol

from src.config import USE_OPENAI_MOCK, USE_EBAY_MOCK
from src.api import openai_client, ebay_client
from src.api.mock_openai import describe_image_mock
from src.api.mock_ebay import search_ebay_mock
from src.services.listing_service import ListingService
from src.services.title_builder import TitleBuilder
from src.services.description_builder import DescriptionBuilder

logger = logging.getLogger(__name__)


class ImageAnalyzer(ABC):
    """Abstract image analyzer."""
    @abstractmethod
    def analyze(self, image_path: str) -> dict:
        pass


class RealImageAnalyzer(ImageAnalyzer):
    """Real image analyzer using OpenAI Vision."""
    def analyze(self, image_path: str) -> dict:
        return openai_client.describe_image(image_path)


class MockImageAnalyzer(ImageAnalyzer):
    """Mock image analyzer for testing."""
    def analyze(self, image_path: str) -> dict:
        return describe_image_mock(image_path)


class EbaySearcher(ABC):
    """Abstract eBay searcher."""
    @abstractmethod
    def search(self, query: str, limit: int) -> list:
        pass


class RealEbaySearcher(EbaySearcher):
    """Real eBay searcher using eBay APIs."""
    def search(self, query: str, limit: int) -> list:
        return ebay_client.search_ebay(query, limit)


class MockEbaySearcher(EbaySearcher):
    """Mock eBay searcher for testing."""
    def search(self, query: str, limit: int) -> list:
        return search_ebay_mock(query, limit)


class Container:
    """Dependency Injection Container."""
    
    def __init__(self):
        self._image_analyzer: ImageAnalyzer = None
        self._ebay_searcher: EbaySearcher = None
        self._listing_service: ListingService = None
        self._title_builder: TitleBuilder = None
        self._description_builder: DescriptionBuilder = None
    
    def get_image_analyzer(self) -> ImageAnalyzer:
        """Get image analyzer (real or mock based on config)."""
        if self._image_analyzer is None:
            if USE_OPENAI_MOCK:
                logger.info("Using MOCK image analyzer")
                self._image_analyzer = MockImageAnalyzer()
            else:
                logger.info("Using REAL image analyzer (OpenAI Vision)")
                self._image_analyzer = RealImageAnalyzer()
        return self._image_analyzer
    
    def get_ebay_searcher(self) -> EbaySearcher:
        """Get eBay searcher (real or mock based on config)."""
        if self._ebay_searcher is None:
            if USE_EBAY_MOCK:
                logger.info("Using MOCK eBay searcher")
                self._ebay_searcher = MockEbaySearcher()
            else:
                logger.info("Using REAL eBay searcher")
                self._ebay_searcher = RealEbaySearcher()
        return self._ebay_searcher
    
    def get_title_builder(self) -> TitleBuilder:
        """Get title builder."""
        if self._title_builder is None:
            self._title_builder = TitleBuilder()
        return self._title_builder
    
    def get_description_builder(self) -> DescriptionBuilder:
        """Get description builder."""
        if self._description_builder is None:
            self._description_builder = DescriptionBuilder()
        return self._description_builder
    
    def get_listing_service(self) -> ListingService:
        """Get listing service with all dependencies wired."""
        if self._listing_service is None:
            self._listing_service = ListingService(
                image_analyzer=self.get_image_analyzer(),
                ebay_searcher=self.get_ebay_searcher(),
                title_builder=self.get_title_builder(),
                description_builder=self.get_description_builder(),
            )
        return self._listing_service
    
    def reset(self):
        """Reset all singletons (useful for testing)."""
        self._image_analyzer = None
        self._ebay_searcher = None
        self._listing_service = None


# Global container instance
_container = Container()


def get_container() -> Container:
    """Get global container instance."""
    return _container
```

**Usage in app.py:**
```python
from src.container import get_container

container = get_container()

@app.route('/api/upload', methods=['POST'])
def upload_file():
    listing_service = container.get_listing_service()
    result = listing_service.generate_from_image(filepath, filename)
```

**Benefits:**
- Easy to swap mock ↔ real
- Easy to test (inject fakes)
- All dependencies centralized
- No global state in services

---

## WEEK 2 SUMMARY

**Deliverables:**
- ✅ `src/services/listing_service.py` - Core business logic
- ✅ `src/services/title_builder.py` - Title generation
- ✅ `src/services/description_builder.py` - Description generation
- ✅ `src/container.py` - Dependency injection
- ✅ Refactored `src/app.py` - Uses services instead of inline logic
- ✅ Comprehensive service tests

**Verification:**
```bash
# Run all tests
pytest tests/ -v --cov=src

# Check coverage > 80%
pytest tests/ --cov=src/services --cov-report=html
```

---

## WEEK 3: CACHING & RATE LIMITING

### Task 3.1: Implement Query Caching (3-4 hours)

**Deliverable:** `src/cache.py`

[See IMPLEMENTATION SECTION 2.6 in main review for full code]

### Task 3.2: Implement Rate Limiting (2-3 hours)

**Deliverable:** Rate limiting decorator in `src/decorators.py`

### Task 3.3: Optimize eBay Token Caching (1-2 hours)

**Deliverable:** Update `src/api/ebay_client.py` with token caching

---

## END-OF-WEEK CHECKLIST

### Week 1
- [ ] All print() replaced with logging
- [ ] Custom exception hierarchy in place
- [ ] Database transactions working
- [ ] Input validation on all endpoints
- [ ] Config validation on startup
- [ ] All Week 1 tests passing

### Week 2
- [ ] ListingService extracted
- [ ] TitleBuilder service created
- [ ] DescriptionBuilder service created
- [ ] DI container implemented
- [ ] app.py refactored to use services
- [ ] All Week 2 tests passing
- [ ] Code coverage > 80%

### Week 3
- [ ] eBay search results cached (24hr TTL)
- [ ] eBay OAuth token cached with refresh
- [ ] Rate limiting on API endpoints
- [ ] Database indexes created
- [ ] Performance benchmarked
- [ ] All Week 3 tests passing

---

## HANDING OFF TO QA/TESTING

After completion, QA team should:
1. Run full test suite: `pytest tests/ -v`
2. Check code coverage: `pytest tests/ --cov=src --cov-report=html`
3. Load test: `locust -f tests/load_test.py`
4. Manual integration testing with real eBay API (sandbox)
5. Security audit (OWASP Top 10)

---

## SUCCESS CRITERIA

Backend is **production-ready** when:
✅ All tests pass (unit + integration)  
✅ Code coverage > 80%  
✅ No unhandled exceptions in production  
✅ All critical bugs fixed  
✅ Database transactions are atomic  
✅ Proper logging throughout  
✅ Input validation on all endpoints  
✅ Services are testable and reusable  
✅ Performance metrics logged  
✅ eBay OAuth token not requested on every call  

Good luck! 🚀
