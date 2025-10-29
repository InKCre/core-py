"""Tests for database URL handling and conversion."""

import os
import sys
from pathlib import Path

# Add parent directory to path to import the function directly
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_database_url() -> str:
    """
    Get database URL from environment variables.
    
    Heroku provides DATABASE_URL with 'postgres://' scheme, but SQLAlchemy 2.0+
    requires 'postgresql://' scheme. This function handles the conversion.
    
    Priority:
    1. DB_CONN_STRING (if set)
    2. DATABASE_URL (from Heroku, with scheme normalization)
    
    Returns:
        Database connection URL string
    """
    # First try DB_CONN_STRING (for backward compatibility)
    db_url = os.getenv("DB_CONN_STRING", "")
    
    # If DB_CONN_STRING is not set, use DATABASE_URL (Heroku default)
    if not db_url:
        db_url = os.getenv("DATABASE_URL", "")
    
    # Convert postgres:// to postgresql:// for SQLAlchemy 2.0+ compatibility
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    return db_url


def test_get_database_url_with_postgres_scheme():
    """Test that postgres:// scheme is converted to postgresql://."""
    # Save original env vars
    original_db_conn = os.environ.get("DB_CONN_STRING")
    original_database_url = os.environ.get("DATABASE_URL")
    
    try:
        # Clear both env vars first
        os.environ.pop("DB_CONN_STRING", None)
        os.environ.pop("DATABASE_URL", None)
        
        # Test with DATABASE_URL using postgres:// scheme (Heroku default)
        heroku_url = "postgres://user:pass@host:5432/dbname"
        os.environ["DATABASE_URL"] = heroku_url
        
        result = get_database_url()
        assert result == "postgresql://user:pass@host:5432/dbname"
        assert result.startswith("postgresql://")
        
    finally:
        # Restore original env vars
        if original_db_conn is not None:
            os.environ["DB_CONN_STRING"] = original_db_conn
        else:
            os.environ.pop("DB_CONN_STRING", None)
            
        if original_database_url is not None:
            os.environ["DATABASE_URL"] = original_database_url
        else:
            os.environ.pop("DATABASE_URL", None)


def test_get_database_url_with_postgresql_scheme():
    """Test that postgresql:// scheme is left unchanged."""
    # Save original env vars
    original_db_conn = os.environ.get("DB_CONN_STRING")
    original_database_url = os.environ.get("DATABASE_URL")
    
    try:
        # Clear both env vars first
        os.environ.pop("DB_CONN_STRING", None)
        os.environ.pop("DATABASE_URL", None)
        
        # Test with DATABASE_URL using postgresql:// scheme (already correct)
        correct_url = "postgresql://user:pass@host:5432/dbname"
        os.environ["DATABASE_URL"] = correct_url
        
        result = get_database_url()
        assert result == correct_url
        assert result.startswith("postgresql://")
        
    finally:
        # Restore original env vars
        if original_db_conn is not None:
            os.environ["DB_CONN_STRING"] = original_db_conn
        else:
            os.environ.pop("DB_CONN_STRING", None)
            
        if original_database_url is not None:
            os.environ["DATABASE_URL"] = original_database_url
        else:
            os.environ.pop("DATABASE_URL", None)


def test_get_database_url_priority():
    """Test that DB_CONN_STRING takes priority over DATABASE_URL."""
    # Save original env vars
    original_db_conn = os.environ.get("DB_CONN_STRING")
    original_database_url = os.environ.get("DATABASE_URL")
    
    try:
        # Set both env vars
        os.environ["DB_CONN_STRING"] = "postgresql://priority:pass@host:5432/db1"
        os.environ["DATABASE_URL"] = "postgres://fallback:pass@host:5432/db2"
        
        result = get_database_url()
        # Should use DB_CONN_STRING (priority)
        assert result == "postgresql://priority:pass@host:5432/db1"
        assert "db1" in result
        assert "db2" not in result
        
    finally:
        # Restore original env vars
        if original_db_conn is not None:
            os.environ["DB_CONN_STRING"] = original_db_conn
        else:
            os.environ.pop("DB_CONN_STRING", None)
            
        if original_database_url is not None:
            os.environ["DATABASE_URL"] = original_database_url
        else:
            os.environ.pop("DATABASE_URL", None)


def test_get_database_url_fallback_to_database_url():
    """Test that DATABASE_URL is used when DB_CONN_STRING is not set."""
    # Save original env vars
    original_db_conn = os.environ.get("DB_CONN_STRING")
    original_database_url = os.environ.get("DATABASE_URL")
    
    try:
        # Clear DB_CONN_STRING, set only DATABASE_URL
        os.environ.pop("DB_CONN_STRING", None)
        os.environ["DATABASE_URL"] = "postgres://user:pass@host:5432/dbname"
        
        result = get_database_url()
        # Should use DATABASE_URL and convert scheme
        assert result == "postgresql://user:pass@host:5432/dbname"
        
    finally:
        # Restore original env vars
        if original_db_conn is not None:
            os.environ["DB_CONN_STRING"] = original_db_conn
        else:
            os.environ.pop("DB_CONN_STRING", None)
            
        if original_database_url is not None:
            os.environ["DATABASE_URL"] = original_database_url
        else:
            os.environ.pop("DATABASE_URL", None)


def test_get_database_url_empty_when_no_env_vars():
    """Test that empty string is returned when no env vars are set."""
    # Save original env vars
    original_db_conn = os.environ.get("DB_CONN_STRING")
    original_database_url = os.environ.get("DATABASE_URL")
    
    try:
        # Clear both env vars
        os.environ.pop("DB_CONN_STRING", None)
        os.environ.pop("DATABASE_URL", None)
        
        result = get_database_url()
        assert result == ""
        
    finally:
        # Restore original env vars
        if original_db_conn is not None:
            os.environ["DB_CONN_STRING"] = original_db_conn
        else:
            os.environ.pop("DB_CONN_STRING", None)
            
        if original_database_url is not None:
            os.environ["DATABASE_URL"] = original_database_url
        else:
            os.environ.pop("DATABASE_URL", None)


def test_get_database_url_with_db_conn_string_postgres_scheme():
    """Test that DB_CONN_STRING with postgres:// scheme is also converted."""
    # Save original env vars
    original_db_conn = os.environ.get("DB_CONN_STRING")
    original_database_url = os.environ.get("DATABASE_URL")
    
    try:
        # Clear DATABASE_URL and set DB_CONN_STRING with postgres:// scheme
        os.environ.pop("DATABASE_URL", None)
        os.environ["DB_CONN_STRING"] = "postgres://user:pass@host:5432/dbname"
        
        result = get_database_url()
        # Should convert scheme even for DB_CONN_STRING
        assert result == "postgresql://user:pass@host:5432/dbname"
        assert result.startswith("postgresql://")
        
    finally:
        # Restore original env vars
        if original_db_conn is not None:
            os.environ["DB_CONN_STRING"] = original_db_conn
        else:
            os.environ.pop("DB_CONN_STRING", None)
            
        if original_database_url is not None:
            os.environ["DATABASE_URL"] = original_database_url
        else:
            os.environ.pop("DATABASE_URL", None)

