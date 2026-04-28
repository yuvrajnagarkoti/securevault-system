-- Database initialization script for SecureVault
-- Creates all required tables with proper constraints for MySQL

-- Create roles table (Dynamic RBAC)
CREATE TABLE IF NOT EXISTS roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    permissions JSON NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seed default roles
INSERT INTO roles (name, permissions) VALUES
    ('Admin', '["upload", "download", "rename", "delete", "view_logs", "manage_roles"]'),
    ('Manager', '["upload", "download", "rename", "delete", "view_logs"]'),
    ('Standard User', '["upload", "download"]')
ON DUPLICATE KEY UPDATE name=name;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    failed_attempts INT NOT NULL DEFAULT 0,
    locked_until TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create files table
CREATE TABLE IF NOT EXISTS files (
    file_id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    size INT NOT NULL,
    owner_id INT NOT NULL,
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64) NOT NULL,
    file_data LONGBLOB,
    is_deleted TINYINT NOT NULL DEFAULT 0,
    FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_files_owner (owner_id),
    INDEX idx_files_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    file_id INT NULL,
    action VARCHAR(50) NOT NULL,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    signature_hash VARCHAR(64) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE SET NULL,
    INDEX idx_audit_logs_user (user_id),
    INDEX idx_audit_logs_file (file_id),
    INDEX idx_audit_logs_timestamp (timestamp DESC),
    INDEX idx_audit_logs_action (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create file_permissions table for access control
CREATE TABLE IF NOT EXISTS file_permissions (
    permission_id INT AUTO_INCREMENT PRIMARY KEY,
    file_id INT NOT NULL,
    user_id INT NOT NULL,
    can_view TINYINT NOT NULL DEFAULT 0,
    can_download TINYINT NOT NULL DEFAULT 0,
    granted_by INT NOT NULL,
    granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_file_user (file_id, user_id),
    INDEX idx_file_permissions_file (file_id),
    INDEX idx_file_permissions_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create default admin user (role_id=1 = Admin)
-- Username: Yuvraj, Password: Password123##
INSERT INTO users (username, password_hash, role_id)
VALUES
    ('Yuvraj', '$2b$12$tt2kxRED7zva90x8.p2YyO38Q3dlWGhwN5Ga4VZU0d/LzPlo8l3e6', 1)
ON DUPLICATE KEY UPDATE username=username;

-- Migration: Add account lockout columns if they don't exist
-- This handles existing databases that were created before lockout was added
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'failed_attempts');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE users ADD COLUMN failed_attempts INT NOT NULL DEFAULT 0', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'locked_until');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE users ADD COLUMN locked_until TIMESTAMP NULL DEFAULT NULL', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;