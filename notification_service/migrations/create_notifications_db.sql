-- ========================================
-- NOTIFICATION MICROSERVICE DATABASE
-- Database: notifications_db
-- Purpose: Separate database for notification microservice
-- Architecture: True microservices
-- Created: 2025-10-12
-- ========================================

-- Create database
CREATE DATABASE IF NOT EXISTS notifications_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE notifications_db;

-- ========================================
-- TABLE 1: notifications
-- ========================================
CREATE TABLE IF NOT EXISTS `notifications` (
  `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL COMMENT 'Reference to users.id in lotto_cc (no FK)',
  `user_email` VARCHAR(255) DEFAULT NULL COMMENT 'Denormalized for convenience',
  
  `title` VARCHAR(255) NOT NULL,
  `body` TEXT NOT NULL,
  `type` ENUM('info', 'alert', 'warning', 'message', 'success', 'reminder', 'trophy') DEFAULT 'info',
  `priority` ENUM('low', 'normal', 'high', 'urgent') DEFAULT 'normal',
  
  `platform` ENUM('phase1', 'phase2', 'mobile', 'web', 'admin') DEFAULT 'phase1',
  `module` VARCHAR(100) DEFAULT NULL,
  `category` VARCHAR(100) DEFAULT NULL,
  
  `is_read` BOOLEAN DEFAULT FALSE,
  `is_delivered` BOOLEAN DEFAULT FALSE,
  `is_archived` BOOLEAN DEFAULT FALSE,
  
  `action_url` VARCHAR(500) DEFAULT NULL,
  `action_text` VARCHAR(100) DEFAULT NULL,
  `meta_data` TEXT DEFAULT NULL,
  
  `read_at` DATETIME DEFAULT NULL,
  `delivered_at` DATETIME DEFAULT NULL,
  `archived_at` DATETIME DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_is_read` (`is_read`),
  INDEX `idx_is_delivered` (`is_delivered`),
  INDEX `idx_priority` (`priority`),
  INDEX `idx_platform` (`platform`),
  INDEX `idx_created_at` (`created_at`),
  INDEX `idx_user_unread` (`user_id`, `is_read`),
  INDEX `idx_user_platform` (`user_id`, `platform`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- TABLE 2: notification_broadcasts
-- ========================================
CREATE TABLE IF NOT EXISTS `notification_broadcasts` (
  `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(255) NOT NULL,
  `body` TEXT NOT NULL,
  `type` ENUM('info', 'alert', 'warning', 'success') DEFAULT 'info',
  `scope` ENUM('all', 'premium', 'viewer', 'admin', 'active') DEFAULT 'all',
  `module` VARCHAR(100) DEFAULT NULL,
  `category` VARCHAR(100) DEFAULT NULL,
  `action_url` VARCHAR(500) DEFAULT NULL,
  `action_text` VARCHAR(100) DEFAULT NULL,
  `sent_count` INT DEFAULT 0,
  `failed_count` INT DEFAULT 0,
  `created_by_user_id` INT DEFAULT NULL COMMENT 'Reference only, no FK',
  `created_by_email` VARCHAR(255) DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX `idx_module` (`module`),
  INDEX `idx_scope` (`scope`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- TABLE 3: notification_templates
-- ========================================
CREATE TABLE IF NOT EXISTS `notification_templates` (
  `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(255) NOT NULL UNIQUE,
  `title` VARCHAR(255) NOT NULL,
  `body` TEXT NOT NULL,
  `type` ENUM('info', 'alert', 'warning', 'message', 'success', 'reminder', 'trophy') DEFAULT 'info',
  `priority` ENUM('low', 'normal', 'high', 'urgent') DEFAULT 'normal',
  `module` VARCHAR(100) DEFAULT NULL,
  `category` VARCHAR(100) DEFAULT NULL,
  `action_url` VARCHAR(500) DEFAULT NULL,
  `action_text` VARCHAR(100) DEFAULT NULL,
  `variables` JSON DEFAULT NULL COMMENT 'Template variables: {game_name}, {date}, etc.',
  `is_active` BOOLEAN DEFAULT TRUE,
  `created_by_user_id` INT DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  INDEX `idx_name` (`name`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- TABLE 4: notification_schedules
-- ========================================
CREATE TABLE IF NOT EXISTS `notification_schedules` (
  `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `template_id` INT DEFAULT NULL,
  `title` VARCHAR(255) NOT NULL,
  `body` TEXT NOT NULL,
  `type` ENUM('info', 'alert', 'warning', 'message', 'success', 'reminder', 'trophy') DEFAULT 'info',
  `priority` ENUM('low', 'normal', 'high', 'urgent') DEFAULT 'normal',
  `scope` ENUM('all', 'premium', 'viewer', 'admin', 'active') DEFAULT 'all',
  `module` VARCHAR(100) DEFAULT NULL,
  `category` VARCHAR(100) DEFAULT NULL,
  `action_url` VARCHAR(500) DEFAULT NULL,
  `action_text` VARCHAR(100) DEFAULT NULL,
  `scheduled_for` DATETIME NOT NULL,
  `status` ENUM('pending', 'sent', 'cancelled', 'failed') DEFAULT 'pending',
  `sent_count` INT DEFAULT 0,
  `sent_at` DATETIME DEFAULT NULL,
  `created_by_user_id` INT DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  FOREIGN KEY (`template_id`) REFERENCES `notification_templates`(`id`) ON DELETE SET NULL,
  INDEX `idx_scheduled_for` (`scheduled_for`),
  INDEX `idx_status` (`status`),
  INDEX `idx_scope` (`scope`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- TABLE 5: notification_settings
-- ========================================
CREATE TABLE IF NOT EXISTS `notification_settings` (
  `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `trigger_name` VARCHAR(100) NOT NULL UNIQUE,
  `description` TEXT NOT NULL,
  `is_enabled` BOOLEAN DEFAULT TRUE,
  `scope` ENUM('all', 'premium', 'viewer', 'admin', 'active') DEFAULT 'all',
  `template_id` INT DEFAULT NULL,
  `cooldown_minutes` INT DEFAULT 0,
  `last_triggered` DATETIME DEFAULT NULL,
  `trigger_count` INT DEFAULT 0,
  `updated_by_user_id` INT DEFAULT NULL,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  FOREIGN KEY (`template_id`) REFERENCES `notification_templates`(`id`) ON DELETE SET NULL,
  INDEX `idx_trigger_name` (`trigger_name`),
  INDEX `idx_is_enabled` (`is_enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- TABLE 6: user_cache (Denormalized)
-- ========================================
CREATE TABLE IF NOT EXISTS `user_cache` (
  `user_id` INT NOT NULL PRIMARY KEY,
  `email` VARCHAR(255) NOT NULL,
  `user_name` VARCHAR(255) DEFAULT NULL,
  `role` VARCHAR(50) DEFAULT NULL COMMENT 'premium, viewer, admin, superuser',
  `is_active` BOOLEAN DEFAULT TRUE,
  `last_synced` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  INDEX `idx_role` (`role`),
  INDEX `idx_is_active` (`is_active`),
  INDEX `idx_last_synced` (`last_synced`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- DEFAULT DATA
-- ========================================

-- Insert default templates
INSERT INTO notification_templates (name, title, body, type, priority, module, category, action_url, action_text, variables) VALUES
('new_predictions', 'New {game_name} Predictions Available!', 'Fresh predictions for {game_name} have been generated using {method}', 'info', 'normal', 'prediction', 'system', '/predictions', 'View Predictions', '{"game_name": "Lotto Max", "method": "Delta System"}'),
('draw_results', '{game_name} Draw Results Available!', 'Check the latest {game_name} draw results from {draw_date}', 'success', 'high', 'draws', 'system', '/results', 'View Results', '{"game_name": "Lotto Max", "draw_date": "2025-10-12"}'),
('subscription_activated', 'Subscription Activated!', 'Your {plan_name} subscription is now active. Enjoy premium features!', 'success', 'high', 'subscription', 'billing', '/subscription', 'View Details', '{"plan_name": "Premium Monthly"}'),
('system_maintenance', 'Scheduled Maintenance', 'The system will be under maintenance on {date} from {start_time} to {end_time}', 'warning', 'high', 'system', 'maintenance', NULL, NULL, '{"date": "2025-10-15", "start_time": "2:00 AM", "end_time": "4:00 AM"}');

-- Insert default auto-notification settings
INSERT INTO notification_settings (trigger_name, description, is_enabled, scope, template_id, cooldown_minutes) VALUES
('auto_prediction_notify', 'Automatically notify when new predictions are generated', TRUE, 'premium', (SELECT id FROM notification_templates WHERE name = 'new_predictions'), 60),
('auto_draw_results', 'Automatically notify when new draw results are available', TRUE, 'all', (SELECT id FROM notification_templates WHERE name = 'draw_results'), 30),
('auto_subscription_activated', 'Automatically notify when subscription is activated', TRUE, 'all', (SELECT id FROM notification_templates WHERE name = 'subscription_activated'), 0),
('auto_ticket_scanned', 'Automatically notify when ticket is scanned', TRUE, 'all', NULL, 0),
('auto_winning_detected', 'Automatically notify when winning ticket is detected', TRUE, 'all', NULL, 0);
