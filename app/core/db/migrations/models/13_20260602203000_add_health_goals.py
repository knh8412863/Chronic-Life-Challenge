from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `user_chronic_disease_goals` (
    `user_id` BIGINT NOT NULL PRIMARY KEY,
    `target_systolic_bp` INT,
    `target_diastolic_bp` INT,
    `target_fasting_glucose` INT,
    `target_postprandial_glucose` INT,
    `target_hba1c` DECIMAL(4,2),
    `target_ldl_cholesterol` INT,
    `target_hdl_cholesterol` INT,
    `target_triglycerides` INT,
    `target_bmi` DECIMAL(5,2),
    `target_weight_kg` DECIMAL(5,2),
    `target_egfr` DECIMAL(6,2),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT `fk_user_chronic_disease_goals_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `user_lifestyle_goals` (
    `user_id` BIGINT NOT NULL PRIMARY KEY,
    `target_steps` INT NOT NULL DEFAULT 10000,
    `target_water_ml` INT NOT NULL DEFAULT 2000,
    `target_exercise_minutes` INT NOT NULL DEFAULT 30,
    `target_sleep_hours` DECIMAL(3,1),
    `target_diet_score` DECIMAL(3,1),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT `fk_user_lifestyle_goals_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `user_lifestyle_goals`;
        DROP TABLE IF EXISTS `user_chronic_disease_goals`;
        """
