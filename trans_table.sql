CREATE TABLE share_transaction (person_id INTEGER, symbol TEXT, company TEXT, shares INTEGER, prices DECIMAL(60, 2), total DECIMAL(60, 2), FOREIGN KEY(person_id) REFERENCES users(id));

ALTER TABLE share_transaction
ADD time DATETIME;



DELETE FROM share_transaction;

DELETE FROM users;

DELETE FROM addcash;


ALTER TABLE share_transaction
ADD TOTAL_COUNT DECIMAL(60, 2);


DROP TABLE share_transaction;



CREATE TABLE addcash (person_id INTEGER, time DATETIME, addmoney DECIMAL(60, 2), FOREIGN KEY(person_id) REFERENCES users(id));



SELECT DISTINCT share_transaction.symbol, share_transaction.shares, share_transaction.prices, addcash.addmoney
FROM share_transaction
JOIN addcash ON addcash.person_id = share_transaction.person_id GROUP BY addcash.addmoney;


