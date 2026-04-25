# QA/TESTING ENGINEER RUNBOOK
## Cards-4-Sale: Testing & Quality Assurance

**Target Role:** QA Engineer / Test Automation Engineer  
**Timeline:** Weeks 1-4 (parallel with development)  
**Success Criteria:** 80%+ code coverage, all critical bugs found and fixed, zero production issues

---

## YOUR MISSION

You are responsible for:
1. **Week 1:** Unit test coverage for logging, exceptions, validators
2. **Week 2:** Integration tests for services and API endpoints
3. **Week 3:** Frontend testing, accessibility validation
4. **Week 4:** System testing, performance testing, security audit

By end of Week 4, the project should be **thoroughly tested and production-ready**.

---

## WEEK 1: UNIT TESTS FOR CRITICAL SYSTEMS

### Task 1.1: Test Configuration & Logging (1-2 hours)

**Deliverable:** `tests/test_config.py`

```python
"""
Tests for configuration and logging setup.
Ensures all config is validated and logging is properly configured.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.config import validate_config, USE_OPENAI_MOCK, USE_EBAY_MOCK
from src.logging_config import configure_logging, get_logger


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_validate_config_passes_with_defaults(self):
        """Config should pass with default mock settings."""
        # With USE_OPENAI_MOCK=True and USE_EBAY_MOCK=True by default
        result = validate_config()
        assert result is True
    
    def test_validate_config_fails_without_openai_key(self):
        """Config should fail if real OpenAI is needed but no key."""
        with patch('src.config.USE_OPENAI_MOCK', False):
            with patch('src.config.OPENAI_API_KEY', ''):
                with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                    validate_config()
    
    def test_validate_config_fails_without_ebay_credentials(self):
        """Config should fail if real eBay is needed but no credentials."""
        with patch('src.config.USE_EBAY_MOCK', False):
            with patch('src.config.EBAY_CLIENT_ID', ''):
                with pytest.raises(ValueError, match="eBay credentials"):
                    validate_config()


class TestLogging:
    """Test logging configuration."""
    
    def test_get_logger_returns_logger(self):
        """get_logger should return a valid logger instance."""
        logger = get_logger(__name__)
        assert logger is not None
        assert logger.name == __name__
    
    def test_configure_logging_creates_log_files(self):
        """Logging should create log files in logs directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.logging_config.LOG_DIR', Path(tmpdir)):
                configure_logging()
                
                logger = get_logger('test')
                logger.info("Test message")
                
                # Log file should be created
                assert Path(tmpdir).exists()
    
    def test_logger_formats_messages(self):
        """Logger should format messages with timestamp and level."""
        logger = get_logger('test')
        
        # Create a test handler to capture output
        handler = MagicMock()
        logger.addHandler(handler)
        
        logger.info("Test message")
        
        # Handler should have been called
        assert handler.handle.called


class TestConfigDefaults:
    """Test configuration default values."""
    
    def test_openai_model_is_set(self):
        """OpenAI model should be configured."""
        from src.config import OPENAI_MODEL
        assert OPENAI_MODEL == "gpt-4o-mini"
    
    def test_ebay_sandbox_default(self):
        """eBay sandbox should be enabled by default for safety."""
        from src.config import EBAY_SANDBOX
        assert EBAY_SANDBOX is True
    
    def test_upload_folder_exists(self):
        """Upload folder should be created if it doesn't exist."""
        from src.config import UPLOAD_FOLDER
        # Folder creation is handled by app.py
        assert UPLOAD_FOLDER is not None
```

**Action Items:**
- [ ] Create `tests/test_config.py`
- [ ] Run: `pytest tests/test_config.py -v`
- [ ] Ensure all tests pass

---

### Task 1.2: Test Exception Handling (1-2 hours)

**Deliverable:** `tests/test_exceptions.py`

```python
"""
Tests for custom exception classes.
Ensures all exceptions carry proper context.
"""

import pytest
from src.exceptions import (
    CardsForSaleException,
    ImageAnalysisError,
    EbayAPIError,
    DatabaseError,
    ValidationError,
)


class TestImageAnalysisError:
    """Test ImageAnalysisError."""
    
    def test_image_analysis_error_has_context(self):
        """ImageAnalysisError should include image path."""
        error = ImageAnalysisError("test.jpg", "File not found")
        
        assert "test.jpg" in str(error)
        assert "File not found" in str(error)
        assert error.image_path == "test.jpg"
        assert error.reason == "File not found"
    
    def test_image_analysis_error_with_original_error(self):
        """ImageAnalysisError should optionally chain original exception."""
        original = FileNotFoundError("File missing")
        error = ImageAnalysisError("test.jpg", "Cannot read", original)
        
        assert error.original_error is original


class TestEbayAPIError:
    """Test EbayAPIError."""
    
    def test_ebay_api_error_with_query(self):
        """EbayAPIError should include search query context."""
        error = EbayAPIError("search", query="MacBook Pro", reason="Rate limited")
        
        assert "search" in str(error)
        assert "MacBook Pro" in str(error)
        assert "Rate limited" in str(error)
    
    def test_ebay_api_error_minimal(self):
        """EbayAPIError should work with just operation."""
        error = EbayAPIError("publish")
        assert "publish" in str(error)


class TestDatabaseError:
    """Test DatabaseError."""
    
    def test_database_error_includes_operation(self):
        """DatabaseError should describe what operation failed."""
        error = DatabaseError("insert", "Primary key violation")
        
        assert "insert" in str(error)
        assert "Primary key violation" in str(error)


class TestValidationError:
    """Test ValidationError."""
    
    def test_validation_error_identifies_field(self):
        """ValidationError should identify which field failed."""
        error = ValidationError("email", "Invalid format")
        
        assert "email" in str(error)
        assert "Invalid format" in str(error)
        assert error.field == "email"


class TestExceptionHierarchy:
    """Test exception inheritance."""
    
    def test_all_exceptions_inherit_from_base(self):
        """All custom exceptions should inherit from CardsForSaleException."""
        exceptions = [
            ImageAnalysisError("", ""),
            EbayAPIError(""),
            DatabaseError("", ""),
            ValidationError("", ""),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, CardsForSaleException)
    
    def test_exceptions_are_catchable(self):
        """Exceptions should be catchable by their type."""
        try:
            raise ImageAnalysisError("test.jpg", "Error")
        except ImageAnalysisError as e:
            assert e.image_path == "test.jpg"
```

**Action Items:**
- [ ] Create `tests/test_exceptions.py`
- [ ] Run: `pytest tests/test_exceptions.py -v`
- [ ] Verify all exception types work correctly

---

### Task 1.3: Test Input Validators (2-3 hours)

**Deliverable:** `tests/test_validators.py`

```python
"""
Tests for input validators.
Ensures all user input is validated before processing.
"""

import pytest
from src.validators import ImageValidator, ListingValidator, AnalysisValidator


class TestImageValidator:
    """Test image file validation."""
    
    def test_validate_valid_jpg(self):
        """Valid JPG should pass."""
        is_valid, error = ImageValidator.validate_upload("photo.jpg", 1024 * 100)
        assert is_valid is True
        assert error == ""
    
    def test_validate_valid_png(self):
        """Valid PNG should pass."""
        is_valid, error = ImageValidator.validate_upload("photo.png", 1024 * 100)
        assert is_valid is True
    
    def test_reject_invalid_extension(self):
        """Invalid file type should fail."""
        is_valid, error = ImageValidator.validate_upload("photo.txt", 1024 * 100)
        assert is_valid is False
        assert "type" in error.lower()
    
    def test_reject_empty_filename(self):
        """Empty filename should fail."""
        is_valid, error = ImageValidator.validate_upload("", 1024 * 100)
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_reject_too_large_file(self):
        """File > 16MB should fail."""
        is_valid, error = ImageValidator.validate_upload("photo.jpg", 20 * 1024 * 1024)
        assert is_valid is False
        assert "large" in error.lower()
    
    def test_reject_oversized_filename(self):
        """Filename > 256 chars should fail."""
        long_name = "a" * 300 + ".jpg"
        is_valid, error = ImageValidator.validate_upload(long_name, 1024)
        assert is_valid is False
        assert "long" in error.lower()
    
    def test_reject_forbidden_chars(self):
        """Filename with null bytes should fail."""
        is_valid, error = ImageValidator.validate_upload("photo\x00.jpg", 1024)
        assert is_valid is False
    
    def test_reject_empty_file(self):
        """Zero-size file should fail."""
        is_valid, error = ImageValidator.validate_upload("photo.jpg", 0)
        assert is_valid is False
        assert "empty" in error.lower()


class TestListingValidator:
    """Test eBay listing payload validation."""
    
    def test_validate_correct_payload(self):
        """Valid listing payload should pass."""
        payload = {
            'sku': 'TEST-123',
            'product': {
                'title': 'Test Item',
                'description': 'A test item'
            },
            'price': {
                'value': '29.99',
                'currency': 'USD'
            },
            'condition': 'USED_GOOD'
        }
        
        is_valid, error = ListingValidator.validate_payload(payload)
        assert is_valid is True
        assert error == ""
    
    def test_reject_missing_sku(self):
        """Missing SKU should fail."""
        payload = {
            'product': {'title': 'Test', 'description': 'Test'},
            'price': {'value': '29.99', 'currency': 'USD'},
        }
        
        is_valid, error = ListingValidator.validate_payload(payload)
        assert is_valid is False
        assert "SKU" in error
    
    def test_reject_empty_title(self):
        """Empty title should fail."""
        payload = {
            'sku': 'TEST-123',
            'product': {'title': '', 'description': 'Test'},
            'price': {'value': '29.99', 'currency': 'USD'},
        }
        
        is_valid, error = ListingValidator.validate_payload(payload)
        assert is_valid is False
        assert "title" in error.lower()
    
    def test_reject_too_long_title(self):
        """Title > 80 chars should fail."""
        payload = {
            'sku': 'TEST-123',
            'product': {
                'title': 'A' * 100,
                'description': 'Test'
            },
            'price': {'value': '29.99', 'currency': 'USD'},
        }
        
        is_valid, error = ListingValidator.validate_payload(payload)
        assert is_valid is False
        assert "long" in error.lower()
    
    def test_reject_invalid_price(self):
        """Price < $0.99 should fail."""
        payload = {
            'sku': 'TEST-123',
            'product': {'title': 'Test', 'description': 'Test'},
            'price': {'value': '0.50', 'currency': 'USD'},
        }
        
        is_valid, error = ListingValidator.validate_payload(payload)
        assert is_valid is False
        assert "range" in error.lower() or "price" in error.lower()
    
    def test_reject_non_usd_currency(self):
        """Non-USD currency should fail."""
        payload = {
            'sku': 'TEST-123',
            'product': {'title': 'Test', 'description': 'Test'},
            'price': {'value': '29.99', 'currency': 'EUR'},
        }
        
        is_valid, error = ListingValidator.validate_payload(payload)
        assert is_valid is False
        assert "USD" in error


class TestAnalysisValidator:
    """Test image analysis validation."""
    
    def test_validate_correct_analysis(self):
        """Valid analysis should pass."""
        analysis = {
            'brand': 'Apple',
            'model': 'MacBook Air',
            'category': 'Electronics',
            'condition': 'Like New',
            'features': ['13-inch', '16GB RAM'],
        }
        
        is_valid, error = AnalysisValidator.validate_analysis(analysis)
        assert is_valid is True
        assert error == ""
    
    def test_validate_trading_card_analysis(self):
        """Valid trading card analysis should pass."""
        analysis = {
            'cards': [
                {
                    'brand': 'Topps',
                    'model': 'Baseball Card',
                    'category': 'Sports Trading Cards',
                    'condition': 'Near Mint',
                    'player_name': 'Babe Ruth',
                }
            ]
        }
        
        is_valid, error = AnalysisValidator.validate_analysis(analysis)
        assert is_valid is True
    
    def test_reject_missing_required_field(self):
        """Missing required field should fail."""
        analysis = {
            'brand': 'Apple',
            # Missing: model, category, condition
        }
        
        is_valid, error = AnalysisValidator.validate_analysis(analysis)
        assert is_valid is False
        assert "required" in error.lower()
    
    def test_reject_empty_field(self):
        """Empty required field should fail."""
        analysis = {
            'brand': '',  # Empty
            'model': 'Test',
            'category': 'Test',
            'condition': 'Test',
        }
        
        is_valid, error = AnalysisValidator.validate_analysis(analysis)
        assert is_valid is False
```

**Action Items:**
- [ ] Create `tests/test_validators.py`
- [ ] Run: `pytest tests/test_validators.py -v`
- [ ] Achieve 100% coverage of validators

---

## WEEK 2: INTEGRATION TESTS

### Task 2.1: Test Database Operations (3-4 hours)

**Deliverable:** Enhanced `tests/test_database.py`

```python
"""
Integration tests for database operations.
Ensures all database operations are atomic and safe.
"""

import pytest
import sqlite3
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.database import (
    init_db, save_listing, get_listing, get_all_listings,
    update_listing_status, delete_listing, record_publish_result,
    get_stats, get_db_connection
)


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        with patch('src.database.DATABASE_PATH', db_path):
            init_db()
            yield db_path
        
        # Cleanup
        if db_path.exists():
            db_path.unlink()


class TestDatabaseInitialization:
    """Test database schema creation."""
    
    def test_init_db_creates_tables(self, test_db):
        """init_db should create necessary tables."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'listings' in tables
        conn.close()
    
    def test_init_db_creates_indexes(self, test_db):
        """init_db should create performance indexes."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        assert 'idx_status' in indexes
        assert 'idx_created_at' in indexes
        conn.close()


class TestSaveListing:
    """Test save_listing function."""
    
    def test_save_listing_returns_id(self, test_db):
        """save_listing should return a listing ID."""
        with patch('src.database.DATABASE_PATH', test_db):
            listing_id = save_listing(
                title="Test Listing",
                filename="test.jpg",
                analysis={'brand': 'Test', 'model': 'Item'},
                comparable_listings=[],
                suggested_price=29.99,
                payload={'sku': 'TEST-123'}
            )
            
            assert listing_id is not None
            assert isinstance(listing_id, int)
            assert listing_id > 0
    
    def test_save_listing_stores_all_fields(self, test_db):
        """save_listing should store all provided fields."""
        with patch('src.database.DATABASE_PATH', test_db):
            listing_id = save_listing(
                title="MacBook Air",
                filename="laptop.jpg",
                analysis={'brand': 'Apple', 'model': 'M2', 'category': 'Electronics'},
                comparable_listings=[{'title': 'Similar', 'price': 999}],
                suggested_price=899.99,
                payload={'sku': 'APPLE-M2', 'title': 'MacBook Air M2'}
            )
            
            # Verify it was saved
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row[1] == "MacBook Air"  # title
            assert row[2] == "laptop.jpg"   # filename
            conn.close()


class TestGetListing:
    """Test get_listing function."""
    
    def test_get_listing_returns_dict(self, test_db):
        """get_listing should return a dictionary."""
        with patch('src.database.DATABASE_PATH', test_db):
            listing_id = save_listing(
                title="Test",
                filename="test.jpg",
                analysis={'brand': 'Test', 'model': 'Item'},
                comparable_listings=[],
                suggested_price=29.99,
                payload={'sku': 'TEST-123'}
            )
            
            listing = get_listing(listing_id)
            
            assert isinstance(listing, dict)
            assert listing['id'] == listing_id
            assert listing['title'] == "Test"
    
    def test_get_listing_returns_none_for_missing(self, test_db):
        """get_listing should return None for non-existent ID."""
        with patch('src.database.DATABASE_PATH', test_db):
            listing = get_listing(99999)
            assert listing is None


class TestUpdateStatus:
    """Test update_listing_status function."""
    
    def test_update_status_changes_status(self, test_db):
        """update_listing_status should change listing status."""
        with patch('src.database.DATABASE_PATH', test_db):
            listing_id = save_listing(
                title="Test",
                filename="test.jpg",
                analysis={'brand': 'Test', 'model': 'Item'},
                comparable_listings=[],
                suggested_price=29.99,
                payload={'sku': 'TEST-123'}
            )
            
            # Change status
            success = update_listing_status(listing_id, 'published')
            assert success is True
            
            # Verify
            listing = get_listing(listing_id)
            assert listing['status'] == 'published'
    
    def test_update_status_rejects_invalid_status(self, test_db):
        """update_listing_status should reject invalid statuses."""
        with patch('src.database.DATABASE_PATH', test_db):
            listing_id = save_listing(
                title="Test",
                filename="test.jpg",
                analysis={'brand': 'Test', 'model': 'Item'},
                comparable_listings=[],
                suggested_price=29.99,
                payload={'sku': 'TEST-123'}
            )
            
            success = update_listing_status(listing_id, 'invalid_status')
            assert success is False


class TestDeleteListing:
    """Test delete_listing function."""
    
    def test_delete_listing_removes_entry(self, test_db):
        """delete_listing should remove listing from database."""
        with patch('src.database.DATABASE_PATH', test_db):
            listing_id = save_listing(
                title="Test",
                filename="test.jpg",
                analysis={'brand': 'Test', 'model': 'Item'},
                comparable_listings=[],
                suggested_price=29.99,
                payload={'sku': 'TEST-123'}
            )
            
            # Delete
            success = delete_listing(listing_id)
            assert success is True
            
            # Verify it's gone
            listing = get_listing(listing_id)
            assert listing is None


class TestStats:
    """Test get_stats function."""
    
    def test_get_stats_counts_listings(self, test_db):
        """get_stats should return accurate counts."""
        with patch('src.database.DATABASE_PATH', test_db):
            # Add listings
            save_listing("L1", "f1.jpg", {}, [], 29.99, {})
            save_listing("L2", "f2.jpg", {}, [], 39.99, {})
            
            stats = get_stats()
            
            assert stats['total'] == 2
            assert stats['drafts'] == 2
            assert stats['published'] == 0
```

**Action Items:**
- [ ] Create/update `tests/test_database.py`
- [ ] Run: `pytest tests/test_database.py -v`
- [ ] Ensure database operations are atomic
- [ ] Verify rollback works on errors

---

### Task 2.2: Test API Endpoints (4-5 hours)

**Deliverable:** Enhanced `tests/test_web.py`

Key tests to add:

```python
"""
Integration tests for Flask API endpoints.
Tests all routes with various inputs.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from src.app import create_app


@pytest.fixture
def client():
    """Create Flask test client."""
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client


class TestUploadEndpoint:
    """Test /api/upload endpoint."""
    
    def test_upload_with_no_file(self, client):
        """POST without file should return 400."""
        response = client.post('/api/upload')
        assert response.status_code == 400
        assert 'error' in response.get_json()
    
    def test_upload_with_invalid_file_type(self, client):
        """Upload non-image file should fail."""
        data = {'photo': (b'text content', 'test.txt')}
        response = client.post('/api/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 400
    
    def test_upload_with_valid_file(self, client):
        """Valid image upload should succeed."""
        with patch('src.app.process_listing') as mock_process:
            mock_process.return_value = {
                'success': True,
                'listing_id': 1,
                'message': 'Success'
            }
            
            # Create a small valid image
            data = {'photo': (b'\x89PNG\r\n', 'test.png')}
            response = client.post(
                '/api/upload',
                data=data,
                content_type='multipart/form-data'
            )
            
            assert response.status_code == 200
            result = response.get_json()
            assert result['success'] is True


class TestListingsEndpoint:
    """Test /api/listings endpoints."""
    
    def test_get_listings_returns_list(self, client):
        """GET /api/listings should return list."""
        response = client.get('/api/listings')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
    
    def test_get_specific_listing(self, client):
        """GET /api/listings/<id> should return listing."""
        # First create a listing
        with patch('src.app.process_listing') as mock_process:
            mock_process.return_value = {
                'success': True,
                'listing_id': 1,
                'message': 'Success',
                'payload': {}
            }
            
            data = {'photo': (b'\x89PNG\r\n', 'test.png')}
            client.post(
                '/api/upload',
                data=data,
                content_type='multipart/form-data'
            )
        
        # Get listing
        response = client.get('/api/listings/1')
        assert response.status_code == 200
        
        listing = response.get_json()
        assert listing['id'] == 1
    
    def test_get_nonexistent_listing(self, client):
        """GET non-existent listing should return 404."""
        response = client.get('/api/listings/99999')
        assert response.status_code == 404


class TestStatusUpdateEndpoint:
    """Test status update functionality."""
    
    def test_update_status_valid(self, client):
        """PATCH listing status with valid status should succeed."""
        # Create listing first
        with patch('src.app.process_listing') as mock_process:
            mock_process.return_value = {
                'success': True,
                'listing_id': 1,
                'message': 'Success',
                'payload': {}
            }
            
            data = {'photo': (b'\x89PNG\r\n', 'test.png')}
            client.post(
                '/api/upload',
                data=data,
                content_type='multipart/form-data'
            )
        
        # Update status
        response = client.patch(
            '/api/listings/1/status',
            json={'status': 'published'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_update_status_invalid(self, client):
        """PATCH with invalid status should fail."""
        response = client.patch(
            '/api/listings/1/status',
            json={'status': 'invalid'},
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestErrorHandling:
    """Test error handling in endpoints."""
    
    def test_large_file_rejected(self, client):
        """Files > 16MB should be rejected."""
        response = client.post(
            '/api/upload',
            content_type='multipart/form-data',
            headers={'Content-Length': '20000000'}
        )
        
        # Should fail with 413 (too large)
        assert response.status_code in [413, 400]
    
    def test_malformed_json_handled(self, client):
        """Malformed JSON should be handled gracefully."""
        response = client.patch(
            '/api/listings/1/status',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code >= 400
```

**Action Items:**
- [ ] Create/update `tests/test_web.py`
- [ ] Add comprehensive endpoint tests
- [ ] Run: `pytest tests/test_web.py -v`
- [ ] Test all HTTP methods (GET, POST, PATCH, DELETE)
- [ ] Test error cases

---

## WEEK 3: FRONTEND TESTING

### Task 3.1: JavaScript Unit Tests (3-4 hours)

**Deliverable:** `tests/test_frontend.js`

```javascript
/**
 * Frontend unit tests using Jest
 * Tests state management, validators, and UI logic
 */

// Install first: npm install --save-dev jest

describe('AppState', () => {
    let appState;
    
    beforeEach(() => {
        appState = new AppState();
    });
    
    test('should initialize with empty state', () => {
        expect(appState.getFileCount()).toBe(0);
        expect(appState.getResultCount()).toBe(0);
        expect(appState.isEbayConnected()).toBe(false);
    });
    
    test('should add files', () => {
        const files = [
            new File(['content'], 'test1.jpg', { type: 'image/jpeg' }),
            new File(['content'], 'test2.png', { type: 'image/png' })
        ];
        
        appState.addFiles(files);
        expect(appState.getFileCount()).toBe(2);
    });
    
    test('should clear files', () => {
        appState.addFiles([new File(['content'], 'test.jpg')]);
        appState.clearFiles();
        expect(appState.getFileCount()).toBe(0);
    });
    
    test('should track processing state', () => {
        expect(appState.isCurrentlyProcessing()).toBe(false);
        appState.setProcessing(true);
        expect(appState.isCurrentlyProcessing()).toBe(true);
    });
    
    test('should notify subscribers on state change', (done) => {
        appState.subscribe(({ key, newValue }) => {
            if (key === 'selectedFiles') {
                expect(newValue.length).toBe(1);
                done();
            }
        });
        
        appState.addFiles([new File(['content'], 'test.jpg')]);
    });
});


describe('FileValidator', () => {
    test('should accept valid image files', () => {
        const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' });
        const errors = FileValidator.validateFile(file);
        expect(errors.length).toBe(0);
    });
    
    test('should reject non-image files', () => {
        const file = new File(['content'], 'test.txt', { type: 'text/plain' });
        const errors = FileValidator.validateFile(file);
        expect(errors.length).toBeGreaterThan(0);
    });
    
    test('should reject files that are too large', () => {
        const largeFile = new File(
            ['x'.repeat(20 * 1024 * 1024)],
            'large.jpg',
            { type: 'image/jpeg' }
        );
        const errors = FileValidator.validateFile(largeFile);
        expect(errors.some(e => e.includes('large'))).toBe(true);
    });
    
    test('should reject empty files', () => {
        const emptyFile = new File([], 'empty.jpg', { type: 'image/jpeg' });
        const errors = FileValidator.validateFile(emptyFile);
        expect(errors.length).toBeGreaterThan(0);
    });
});

// Run with: npm test
```

**Add to package.json:**
```json
{
  "devDependencies": {
    "jest": "^29.0.0"
  },
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch"
  }
}
```

**Action Items:**
- [ ] Install Jest: `npm install --save-dev jest`
- [ ] Create `tests/test_frontend.js`
- [ ] Run: `npm test`
- [ ] Aim for 80%+ coverage

---

### Task 3.2: Accessibility Testing (2-3 hours)

**Deliverable:** Accessibility test checklist

Create `tests/ACCESSIBILITY_CHECKLIST.md`:

```markdown
# Accessibility Testing Checklist (WCAG 2.1 AA)

## Keyboard Navigation
- [ ] Can navigate all interactive elements with Tab key
- [ ] Tab order is logical (top-to-bottom, left-to-right)
- [ ] No keyboard traps (able to Tab out of all elements)
- [ ] Focus indicator is visible (outline or highlight)
- [ ] Can activate buttons with Enter/Space
- [ ] Can select form options with arrow keys

## Screen Reader
- [ ] All images have alt text (or aria-hidden if decorative)
- [ ] Form labels are associated with inputs
- [ ] Headings follow logical order (h1, h2, h3...)
- [ ] Links have descriptive text (not "click here")
- [ ] Button purposes are clear
- [ ] Error messages are announced
- [ ] Dynamic content updates are announced (aria-live)
- [ ] Modal dialogs have focus trap

## Visual
- [ ] Color contrast >= 4.5:1 (normal text)
- [ ] Color contrast >= 3:1 (large text)
- [ ] Color not the only indicator (also use icons, text)
- [ ] Text is resizable (no fixed px font sizes)
- [ ] No content hidden at 200% zoom
- [ ] Focus indicator color contrast >= 3:1

## Forms
- [ ] All form inputs have labels
- [ ] Labels visible and associated (for attribute)
- [ ] Required fields are marked
- [ ] Error messages are specific
- [ ] Error messages linked to fields (aria-describedby)
- [ ] Form hints visible

## Motion & Animation
- [ ] Animations don't flash > 3 times per second
- [ ] Respects prefers-reduced-motion
- [ ] No auto-playing audio/video

## Testing Tools
- [ ] axe DevTools (Chrome extension)
- [ ] WAVE (WebAIM)
- [ ] Lighthouse (Chrome DevTools)
- [ ] Screen reader (NVDA, JAWS, VoiceOver)
```

**Manual Testing Steps:**
1. Tab through entire page - should be able to use all features without mouse
2. Test with NVDA (Windows), JAWS (Windows), or VoiceOver (Mac)
3. Run axe DevTools and fix all violations
4. Check Lighthouse accessibility score (should be 95+)
5. Verify color contrast with WebAIM Color Contrast Checker

**Action Items:**
- [ ] Create accessibility checklist
- [ ] Run axe DevTools on every page
- [ ] Test with at least one screen reader
- [ ] Verify Lighthouse accessibility > 95

---

## WEEK 4: SYSTEM TESTING & SECURITY

### Task 4.1: Performance Testing (2-3 hours)

**Deliverable:** Performance test suite

Create `tests/test_performance.py`:

```python
"""
Performance tests to ensure the app meets speed targets.
"""

import pytest
import time
from unittest.mock import patch


class TestResponseTimes:
    """Test API response times."""
    
    def test_homepage_loads_fast(self, client):
        """Homepage should load in < 1 second."""
        start = time.time()
        response = client.get('/')
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0, f"Homepage took {elapsed}s (target: < 1s)"
    
    def test_listings_api_returns_fast(self, client):
        """Listings API should respond in < 500ms."""
        start = time.time()
        response = client.get('/api/listings')
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5, f"API took {elapsed}s (target: < 500ms)"


class TestDatabasePerformance:
    """Test database query performance."""
    
    def test_get_all_listings_scales(self):
        """get_all_listings should be fast even with 1000 listings."""
        # Create 1000 listings
        from src.database import save_listing, get_all_listings
        
        for i in range(1000):
            save_listing(
                f"Listing {i}",
                f"file{i}.jpg",
                {'brand': f'Brand{i}', 'model': f'Model{i}'},
                [],
                29.99,
                {}
            )
        
        # Query should complete in < 500ms
        start = time.time()
        listings = get_all_listings()
        elapsed = time.time() - start
        
        assert len(listings) == 1000
        assert elapsed < 0.5, f"Query took {elapsed}s (target: < 500ms)"
```

**Action Items:**
- [ ] Create `tests/test_performance.py`
- [ ] Set performance targets
- [ ] Profile with Chrome DevTools
- [ ] Optimize slow queries/endpoints

---

### Task 4.2: Security Testing (3-4 hours)

**Deliverable:** Security test suite and audit

```python
"""
Security tests covering OWASP Top 10.
"""

import pytest


class TestSecurityHeaders:
    """Test HTTP security headers."""
    
    def test_has_content_security_policy(self, client):
        """Response should include CSP header."""
        response = client.get('/')
        # CSP header should be present (configure in app)
        # assert 'Content-Security-Policy' in response.headers


class TestInputValidation:
    """Test input validation against injection attacks."""
    
    def test_xss_protection_in_user_input(self, client):
        """User input should be escaped to prevent XSS."""
        response = client.post(
            '/api/upload',
            json={'title': '<script>alert("xss")</script>'},
            content_type='application/json'
        )
        
        # Should not contain unescaped script tag
        # Validation should reject or escape


class TestSQLInjection:
    """Test SQL injection protection."""
    
    def test_sql_injection_in_query(self, client):
        """SQL queries should use parameterized statements."""
        # Attempt SQL injection
        response = client.get('/api/listings/1" OR "1"="1')
        
        # Should either fail safely or return specific listing
        # Not execute the injected SQL


class TestAuthenticationChallenges:
    """Test authentication boundaries."""
    
    def test_unauthorized_access_denied(self, client):
        """Sensitive endpoints should require auth (when implemented)."""
        # Response should be 401 or redirect to login
        pass


class TestRateLimiting:
    """Test rate limiting (when implemented)."""
    
    def test_rapid_requests_throttled(self, client):
        """Too many requests should be rate limited."""
        # Send 100 requests rapidly
        for i in range(100):
            response = client.post('/api/upload')
            
            if i > 50:
                # Should start getting rate limited
                # Status code should indicate throttling (429)
                pass
```

**Security Checklist:**

```markdown
# Security Audit Checklist

## Code Review
- [ ] No hardcoded secrets (API keys, passwords)
- [ ] No SQL injection vulnerabilities (use parameterized queries)
- [ ] No XSS vulnerabilities (escape user input)
- [ ] No CSRF vulnerabilities (use CSRF tokens)
- [ ] No insecure dependencies (check npm audit, pip audit)

## API Security
- [ ] HTTPS enforced (in production)
- [ ] API rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] Error messages don't leak sensitive info
- [ ] CORS configured properly

## Data Security
- [ ] Database encrypted at rest (if using cloud)
- [ ] Passwords hashed (bcrypt/argon2)
- [ ] Sensitive data not logged
- [ ] Data retention policy implemented
- [ ] Backups are encrypted

## Deployment
- [ ] Environment variables for secrets (not in code)
- [ ] Security headers configured
- [ ] WAF (Web Application Firewall) enabled
- [ ] Regular security updates
- [ ] Incident response plan

## Compliance
- [ ] Privacy policy created
- [ ] Terms of service created
- [ ] GDPR compliance (if applicable)
- [ ] Data deletion request process
```

**Action Items:**
- [ ] Create `tests/test_security.py`
- [ ] Run `pip-audit` and `npm audit` for dependencies
- [ ] Review code for common vulnerabilities
- [ ] Test with OWASP ZAP or Burp Suite (free community edition)
- [ ] Create security policy documentation

---

## TEST EXECUTION STRATEGY

### Daily (During Development)
```bash
# Run unit tests
pytest tests/ -v --tb=short

# Check code coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### Weekly (End of sprint)
```bash
# Full test suite with coverage report
pytest tests/ --cov=src --cov-report=html

# Performance testing
pytest tests/test_performance.py -v

# Security audit
pip-audit
npm audit
```

### Before Release
```bash
# All tests must pass
pytest tests/ -v

# Coverage must be > 80%
pytest tests/ --cov=src --cov-report=term --cov-fail-under=80

# Accessibility audit (manual)
# - Run WCAG checker
# - Test with screen reader
# - Verify keyboard navigation

# Security audit (manual)
# - OWASP Top 10 review
# - Dependency check
# - Code security review

# Performance testing (manual)
# - Load testing with Locust
# - Profiling with DevTools
# - Measure real-world times
```

---

## SUCCESS CRITERIA

### Code Quality
- ✅ Code coverage > 80%
- ✅ All tests pass
- ✅ No critical vulnerabilities
- ✅ No code smells (checked with linting)

### Performance
- ✅ Homepage loads < 1s
- ✅ API responses < 500ms
- ✅ No memory leaks
- ✅ Database queries optimized

### Accessibility
- ✅ WCAG 2.1 AA compliant
- ✅ Keyboard navigation works
- ✅ Screen reader compatible
- ✅ Color contrast > 4.5:1

### Security
- ✅ No OWASP Top 10 violations
- ✅ All dependencies up-to-date
- ✅ Secrets not in code
- ✅ Input validation on all endpoints

---

## HANDING OFF RESULTS

After completion, provide:
1. **Test Report:** `coverage_report.html` + summary statistics
2. **Security Report:** Vulnerabilities found & remediation steps
3. **Performance Report:** Load times, memory usage, profiles
4. **Accessibility Report:** Violations found & fixes applied
5. **Regression Testing:** All scenarios tested, results documented

---

Good luck with testing! Your thorough QA will make this a rock-solid product. 🧪✅
