DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;

CREATE TABLE orders (
                        id         BIGINT AUTO_INCREMENT PRIMARY KEY,
                        customer   VARCHAR(100) NOT NULL,
                        item       VARCHAR(100) NOT NULL,
                        amount     DECIMAL(10, 2) NOT NULL,
                        status     VARCHAR(20) NOT NULL
);

CREATE TABLE products (
                          id       BIGINT AUTO_INCREMENT PRIMARY KEY,
                          name     VARCHAR(100) NOT NULL,
                          price    DECIMAL(10, 2) NOT NULL,
                          stock    INT NOT NULL
);