from .database import get_connection, is_in_transaction, set_in_transaction, TransactionRequiredError

__all__ = ["UnitOfWork", "TransactionRequiredError", "require_transaction"]

from .database import require_transaction # re-export

class UnitOfWork:
    def __enter__(self):
        if is_in_transaction():
            raise RuntimeError("Nested UnitOfWork is not allowed")
            
        self.conn = get_connection()
        self.conn.execute("BEGIN")
        set_in_transaction(True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self.conn.rollback()
            else:
                self.conn.commit()
        finally:
            set_in_transaction(False)