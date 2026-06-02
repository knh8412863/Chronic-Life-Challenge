from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `weekly_reports` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `week_start_date` DATE NOT NULL,
    `week_end_date` DATE NOT NULL,
    `source_summary` JSON NOT NULL,
    `report_text` LONGTEXT NOT NULL,
    `provider` VARCHAR(20) NOT NULL,
    `model_name` VARCHAR(50) NOT NULL,
    `input_tokens` INT,
    `output_tokens` INT,
    `cache_read_tokens` INT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_weekly_reports_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uid_weekly_reports_user_week` (`user_id`, `week_start_date`)
) CHARACTER SET utf8mb4;
        CREATE INDEX `idx_weekly_reports_user_created` ON `weekly_reports` (`user_id`, `created_at`);
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `weekly_reports`;
        """
