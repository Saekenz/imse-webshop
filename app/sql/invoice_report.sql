SELECT u.user_id, u.first_name AS "First Name", u.last_name AS "Last Name", COUNT(i.invoice_id) AS unpaid_invoice_count
FROM User_ u
LEFT JOIN Order_ o ON u.user_id = o.user_id
LEFT JOIN Invoice i ON o.order_id = i.order_id
WHERE o.date_placed >= DATE_ADD(NOW(), INTERVAL -1 YEAR)
  AND i.payment_status != "paid"
GROUP BY u.user_id
ORDER BY unpaid_invoice_count DESC;
