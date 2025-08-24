-- CREATE DATABASE wealth_tracker;
-- ALTER TABLE wealth_tracker.upload_history DROP COLUMN prev_bank_balance
-- ALTER TABLE wealth_tracker.configs ADD COLUMN prev_bank_balance DECIMAL(15,4) DEFAULT 0.0;
-- ALTER TABLE wealth_tracker.configs ADD COLUMN bank_balance  DECIMAL(15,4) DEFAULT 0.0;



select * from wealth_tracker.configs;
select * from wealth_tracker.users;
select * from wealth_tracker.upload_history;
select * from wealth_tracker.expense;
select * from wealth_tracker.savings;
select * from wealth_tracker.monthly_distribution;
select * from wealth_tracker.yearly_distribution;