"""The MySQL tables, created in order (clients first, as transactions refer to them)."""

TABLES = (
    """
    CREATE TABLE IF NOT EXISTS clients (
        client_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        risk ENUM('Conservative', 'Balanced', 'Growth') NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INT AUTO_INCREMENT PRIMARY KEY,
        client_id INT NOT NULL,
        trade_date DATE NOT NULL,
        ticker VARCHAR(10) NOT NULL,
        side ENUM('Buy', 'Sell') NOT NULL,
        quantity DECIMAL(18, 4) NOT NULL CHECK (quantity > 0),
        price DECIMAL(18, 4) NOT NULL CHECK (price > 0),
        FOREIGN KEY (client_id) REFERENCES clients (client_id) ON DELETE CASCADE,
        INDEX (client_id, trade_date)
    )
    """,
)
