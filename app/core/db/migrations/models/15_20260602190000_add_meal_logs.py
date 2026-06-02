from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `meal_logs` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `food_analysis_result_id` BIGINT,
    `meal_date` DATE NOT NULL,
    `meal_type` VARCHAR(20) NOT NULL,
    `food_name` VARCHAR(100) NOT NULL,
    `amount` VARCHAR(50),
    `calories` INT,
    `carbs_g` DECIMAL(6,2),
    `protein_g` DECIMAL(6,2),
    `fat_g` DECIMAL(6,2),
    `sodium_mg` DECIMAL(8,2),
    `sugar_g` DECIMAL(6,2),
    `fiber_g` DECIMAL(6,2),
    `memo` VARCHAR(255),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_meal_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE INDEX `idx_meal_logs_user_date` ON `meal_logs` (`user_id`, `meal_date`);
        CREATE INDEX `idx_meal_logs_analysis_result` ON `meal_logs` (`food_analysis_result_id`);
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `meal_logs`;
        """
