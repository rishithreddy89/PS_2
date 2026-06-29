-- Initialize LexMind AI Database

CREATE DATABASE IF NOT EXISTS lexmind_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE lexmind_db;

-- Grant privileges
GRANT ALL PRIVILEGES ON lexmind_db.* TO 'lexmind'@'%';
FLUSH PRIVILEGES;
