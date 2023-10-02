
CREATE DATABASE tracker_db;
CREATE USER tracker_user WITH PASSWORD 'tracker_pass' SUPERUSER;
ALTER ROLE tracker_user SET client_encoding TO 'utf8';
ALTER ROLE tracker_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE tracker_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE tracker_db TO tracker_user;

