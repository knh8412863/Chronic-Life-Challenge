from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `data_exports` (
            `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `export_id` VARCHAR(50) NOT NULL UNIQUE,
            `format` VARCHAR(20) NOT NULL,
            `start_date` DATE NOT NULL,
            `end_date` DATE NOT NULL,
            `data_types` JSON NOT NULL,
            `status` VARCHAR(20) NOT NULL DEFAULT 'COMPLETED',
            `file_path` VARCHAR(500),
            `file_size_bytes` BIGINT,
            `download_count` INT NOT NULL DEFAULT 0,
            `send_email` BOOL NOT NULL DEFAULT 0,
            `password_protected` BOOL NOT NULL DEFAULT 0,
            `expires_at` DATETIME(6) NOT NULL,
            `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            `user_id` BIGINT NOT NULL,
            CONSTRAINT `fk_data_exports_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
            INDEX `idx_data_exports_user_created` (`user_id`, `created_at`),
            INDEX `idx_data_exports_status` (`status`),
            INDEX `idx_data_exports_expires` (`expires_at`)
        ) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `data_export_logs` (
            `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `export_id` VARCHAR(50) NOT NULL,
            `event` VARCHAR(50) NOT NULL,
            `error_message` LONGTEXT,
            `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            INDEX `idx_data_export_logs_export_id` (`export_id`)
        ) CHARACTER SET utf8mb4;
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `data_export_logs`;
        DROP TABLE IF EXISTS `data_exports`;
        """
