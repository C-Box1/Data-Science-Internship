-- =============================================================================
-- Watch Consignment Management — PostgreSQL Schema
-- Run this file once to create all tables.
-- =============================================================================

-- Drop tables in reverse dependency order if recreating from scratch
DROP TABLE IF EXISTS sold_elements        CASCADE;
DROP TABLE IF EXISTS present_elements     CASCADE;
DROP TABLE IF EXISTS abbreviations        CASCADE;
DROP TABLE IF EXISTS products_information CASCADE;
DROP TABLE IF EXISTS market_information   CASCADE;

-- =============================================================================
-- Table 1: products_information
-- Stores all product references — both WATCH and COFFRET kinds.
-- COFFRET = a set containing a watch and its coffret presentation box.
-- =============================================================================
CREATE TABLE products_information (
    products_id        SERIAL          NOT NULL,
    reference          VARCHAR(20)     NOT NULL,
    kind               VARCHAR(20)     NOT NULL CHECK (kind IN ('WATCH', 'COFFRET')),
    collection         VARCHAR(100)    NOT NULL,
    gender             VARCHAR(20)     NOT NULL CHECK (gender IN ('LADIES', 'GENTS', 'UNISEX')),
    movement           VARCHAR(50)     NOT NULL CHECK (movement IN ('QUARTZ', 'AUTOMATIC', 'MECHANICAL')),
    dial               VARCHAR(100)    NULL,
    bracelet           VARCHAR(100)    NULL,
    color              VARCHAR(50)     NULL,
    case_size          VARCHAR(30)     NULL,
    date_of_creation   DATE            NULL,
    date_of_reception  DATE            NULL,

    CONSTRAINT pk_products         PRIMARY KEY (products_id),
    CONSTRAINT uq_products_ref     UNIQUE (reference)
);

-- =============================================================================
-- Table 2: market_information
-- Stores all shop locations extracted from monthly report headers.
-- shop_id is used directly as PK — it is a stable 4-digit distributor code.
-- =============================================================================
CREATE TABLE market_information (
    shop_id      VARCHAR(10)     NOT NULL,
    mall_name    VARCHAR(150)    NOT NULL,
    city         VARCHAR(100)    NULL,
    country      VARCHAR(100)    NOT NULL DEFAULT 'Saudi Arabia',
    distributor  VARCHAR(100)    NULL,
    shop_type    VARCHAR(20)     NOT NULL DEFAULT 'retail'
                                 CHECK (shop_type IN ('retail', 'warehouse', 'online')),

    CONSTRAINT pk_market PRIMARY KEY (shop_id)
);

-- =============================================================================
-- Table 3: present_elements
-- Monthly closing stock snapshots — one row per product per shop per month.
-- =============================================================================
CREATE TABLE present_elements (
    present_id      SERIAL          NOT NULL,
    item_reference  VARCHAR(20)     NOT NULL,
    shop_id         VARCHAR(10)     NOT NULL,
    report_month    DATE            NOT NULL,
    closing_stock   INTEGER         NOT NULL CHECK (closing_stock >= 0),
    reception_date  DATE            NULL,
    removal_date    DATE            NULL,

    CONSTRAINT pk_present
        PRIMARY KEY (present_id),
    CONSTRAINT fk_present_product
        FOREIGN KEY (item_reference) REFERENCES products_information (reference)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_present_shop
        FOREIGN KEY (shop_id) REFERENCES market_information (shop_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_present_snapshot
        UNIQUE (item_reference, shop_id, report_month)
);

-- =============================================================================
-- Table 4: sold_elements
-- Monthly sales records — one row per product per shop per month.
-- sale_source: 'monthly_report' = loaded from Excel, 'manual' = Flask entry.
-- =============================================================================
CREATE TABLE sold_elements (
    sale_id         SERIAL          NOT NULL,
    item_reference  VARCHAR(20)     NOT NULL,
    shop_id         VARCHAR(10)     NOT NULL,
    sale_month      DATE            NOT NULL,
    quantity_sold   INTEGER         NOT NULL CHECK (quantity_sold >= 0),
    sale_source     VARCHAR(20)     NOT NULL DEFAULT 'monthly_report'
                                    CHECK (sale_source IN ('monthly_report', 'manual')),

    CONSTRAINT pk_sold
        PRIMARY KEY (sale_id),
    CONSTRAINT fk_sold_product
        FOREIGN KEY (item_reference) REFERENCES products_information (reference)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_sold_shop
        FOREIGN KEY (shop_id) REFERENCES market_information (shop_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_sold_record
        UNIQUE (item_reference, shop_id, sale_month)
);

-- =============================================================================
-- Indexes for common query patterns
-- =============================================================================
CREATE INDEX idx_present_ref       ON present_elements (item_reference);
CREATE INDEX idx_present_shop      ON present_elements (shop_id);
CREATE INDEX idx_present_month     ON present_elements (report_month);
CREATE INDEX idx_sold_ref          ON sold_elements (item_reference);
CREATE INDEX idx_sold_shop         ON sold_elements (shop_id);
CREATE INDEX idx_sold_month        ON sold_elements (sale_month);
CREATE INDEX idx_products_kind     ON products_information (kind);
CREATE INDEX idx_products_coll     ON products_information (collection);

-- =============================================================================
-- Table 5: abbreviations
-- Maps short codes to full terms (case-insensitive lookup in Python).
-- One full_term may have many abbreviations (e.g. BRCLT and BRACE → BRACELET).
-- field_category groups abbreviations by product field (bracelet, color, etc.).
-- =============================================================================
CREATE TABLE abbreviations (
    abbrev_id       SERIAL          NOT NULL,
    abbreviation    VARCHAR(50)     NOT NULL,
    full_term       VARCHAR(150)    NOT NULL,
    field_category  VARCHAR(50)     NOT NULL
                    CHECK (field_category IN (
                        'bracelet', 'color', 'movement', 'dial', 'collection', 'general'
                    )),
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_abbreviations PRIMARY KEY (abbrev_id),
    CONSTRAINT uq_abbrev_per_category UNIQUE (abbreviation, field_category)
);

CREATE INDEX idx_abbrev_lookup ON abbreviations (field_category);
CREATE INDEX idx_abbrev_term   ON abbreviations (full_term);