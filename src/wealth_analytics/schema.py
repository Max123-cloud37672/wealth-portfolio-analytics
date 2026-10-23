"""The MySQL tables, created in order (a table must exist before others refer to it)."""

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
    """
    CREATE TABLE IF NOT EXISTS securities (
        ticker VARCHAR(10) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        asset_type ENUM('Stock', 'ETF') NOT NULL,
        sector VARCHAR(50) NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS prices (
        ticker VARCHAR(10) NOT NULL,
        price_date DATE NOT NULL,
        close DECIMAL(18, 4) NOT NULL CHECK (close > 0),
        PRIMARY KEY (ticker, price_date),
        FOREIGN KEY (ticker) REFERENCES securities (ticker) ON DELETE CASCADE
    )
    """,
)
