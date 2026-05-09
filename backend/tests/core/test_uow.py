import pytest
from app.core.uow import UnitOfWork, TransactionRequiredError, require_transaction
from app.core.database import get_connection

def test_uow_commits_on_success():
    conn = get_connection()
    conn.execute("CREATE TABLE IF NOT EXISTS uow_test (id INTEGER PRIMARY KEY)")
    conn.execute("DELETE FROM uow_test")
    
    with UnitOfWork():
        conn.execute("INSERT INTO uow_test (id) VALUES (1)")
        
    row = conn.execute("SELECT * FROM uow_test WHERE id=1").fetchone()
    assert row is not None

def test_uow_rollbacks_on_exception():
    conn = get_connection()
    conn.execute("CREATE TABLE IF NOT EXISTS uow_test (id INTEGER PRIMARY KEY)")
    conn.execute("DELETE FROM uow_test")
    
    try:
        with UnitOfWork():
            conn.execute("INSERT INTO uow_test (id) VALUES (2)")
            raise ValueError("Trigger rollback")
    except ValueError:
        pass
        
    row = conn.execute("SELECT * FROM uow_test WHERE id=2").fetchone()
    assert row is None

def test_uow_prevents_nesting():
    with pytest.raises(RuntimeError, match="Nested UnitOfWork is not allowed"):
        with UnitOfWork():
            with UnitOfWork():
                pass

def test_require_transaction_enforcement():
    with pytest.raises(TransactionRequiredError):
        require_transaction()
        
    with UnitOfWork():
        require_transaction() # Should not raise