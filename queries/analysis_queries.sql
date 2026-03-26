-- Total restaurants
SELECT COUNT(*) FROM restaurants;

-- Top locations
SELECT location, COUNT(*) AS total_restaurants
FROM restaurants
GROUP BY location
ORDER BY total_restaurants DESC
LIMIT 10;

-- Average rating by location
SELECT location, AVG(rate) AS avg_rating
FROM restaurants
GROUP BY location
ORDER BY avg_rating DESC;

-- Online order availability
SELECT online_order, COUNT(*)
FROM restaurants
GROUP BY online_order;

-- Top expensive restaurants
SELECT restaurant_name, approx_cost_for_two
FROM restaurants
ORDER BY approx_cost_for_two DESC
LIMIT 10;