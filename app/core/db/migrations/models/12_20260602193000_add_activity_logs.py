from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `activity_logs` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `record_date` DATE NOT NULL,
    `alcohol_frequency` INT,
    `alcohol_amount` INT,
    `walking_days` INT,
    `sedentary_hours` DECIMAL(4,1),
    `sleep_hours` DECIMAL(3,1),
    `stress_level` INT,
    `diet_score` DECIMAL(3,1),
    `memo` VARCHAR(255),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_activity_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uid_activity_logs_user_date` (`user_id`, `record_date`)
) CHARACTER SET utf8mb4;
        CREATE INDEX `idx_activity_logs_user_date` ON `activity_logs` (`user_id`, `record_date`);
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `activity_logs`;
        """
