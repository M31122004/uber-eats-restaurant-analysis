CREATE DATABASE uber_eats;

USE uber_eats;

CREATE TABLE restaurants (
    restaurant_name VARCHAR(255),
    location VARCHAR(255),
    cuisines VARCHAR(255),
    rate FLOAT,
    approx_cost_for_two INT,
    online_order VARCHAR(10),
    book_table VARCHAR(10)
);