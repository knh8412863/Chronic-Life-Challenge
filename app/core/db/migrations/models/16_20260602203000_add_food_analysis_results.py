from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `food_analysis_results` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `task_uuid` VARCHAR(36) NOT NULL UNIQUE,
    `status` VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',
    `meal_date` DATE,
    `meal_type` VARCHAR(20),
    `food_name` VARCHAR(100) NOT NULL,
    `amount` VARCHAR(50),
    `calories` INT,
    `carbs_g` DECIMAL(6,2),
    `protein_g` DECIMAL(6,2),
    `fat_g` DECIMAL(6,2),
    `sodium_mg` DECIMAL(8,2),
    `sugar_g` DECIMAL(6,2),
    `fiber_g` DECIMAL(6,2),
    `health_score` INT NOT NULL,
    `risk_flags` JSON NOT NULL,
    `advice_text` VARCHAR(500) NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_food_analysis_results_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE INDEX `idx_food_analysis_results_user_created` ON `food_analysis_results` (`user_id`, `created_at`);
        ALTER TABLE `meal_logs`
            ADD CONSTRAINT `fk_meal_logs_food_analysis_result`
            FOREIGN KEY (`food_analysis_result_id`) REFERENCES `food_analysis_results` (`id`) ON DELETE SET NULL;
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `meal_logs` DROP FOREIGN KEY `fk_meal_logs_food_analysis_result`;
        DROP TABLE IF EXISTS `food_analysis_results`;
        """
