-- Canonical schema. The loader replaces placeholders with staging/final names.
-- Secondary indexes are created after bulk insertion by python/load_mysql.py.

CREATE TABLE {{RAW_TABLE}} (
    row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    source_sheet VARCHAR(40) NOT NULL,
    invoice VARCHAR(24) NULL,
    stock_code VARCHAR(40) NULL,
    description TEXT NULL,
    quantity INT NULL,
    invoice_date DATETIME NULL,
    price DECIMAL(18, 6) NULL,
    customer_id BIGINT NULL,
    country VARCHAR(100) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE {{CLEAN_TABLE}} (
    row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    source_sheet VARCHAR(40) NOT NULL,
    invoice VARCHAR(24) NULL,
    stock_code VARCHAR(40) NULL,
    description TEXT NULL,
    quantity INT NULL,
    invoice_date DATETIME NULL,
    price DECIMAL(18, 6) NULL,
    customer_id BIGINT NULL,
    country VARCHAR(100) NULL,
    is_cancellation TINYINT(1) NOT NULL,
    is_guest TINYINT(1) NOT NULL,
    is_non_product TINYINT(1) NOT NULL,
    line_revenue DECIMAL(24, 6) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX ix_raw_invoice ON {{RAW_TABLE}} (invoice);
CREATE INDEX ix_raw_customer ON {{RAW_TABLE}} (customer_id);
CREATE INDEX ix_raw_date ON {{RAW_TABLE}} (invoice_date);
CREATE INDEX ix_raw_product ON {{RAW_TABLE}} (stock_code);
CREATE INDEX ix_clean_invoice ON {{CLEAN_TABLE}} (invoice);
CREATE INDEX ix_clean_customer ON {{CLEAN_TABLE}} (customer_id);
CREATE INDEX ix_clean_date ON {{CLEAN_TABLE}} (invoice_date);
CREATE INDEX ix_clean_product ON {{CLEAN_TABLE}} (stock_code);
