from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `virtual_pets` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `pet_type` VARCHAR(20) NOT NULL,
    `pet_name` VARCHAR(50) NOT NULL,
    `level` INT NOT NULL DEFAULT 1,
    `experience` INT NOT NULL DEFAULT 0,
    `next_level_experience` INT NOT NULL DEFAULT 1000,
    `growth_stage` VARCHAR(20) NOT NULL DEFAULT 'STAGE_1',
    `health_percent` INT NOT NULL DEFAULT 0,
    `happiness_percent` INT NOT NULL DEFAULT 0,
    `last_updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL UNIQUE,
    CONSTRAINT `fk_virtual_pets_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `virtual_pet_activity_logs` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `activity_type` VARCHAR(30) NOT NULL,
    `description` VARCHAR(255) NOT NULL,
    `experience_delta` INT NOT NULL DEFAULT 0,
    `source_type` VARCHAR(30),
    `source_id` BIGINT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `pet_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_virtual_pet_activity_logs_pet` FOREIGN KEY (`pet_id`) REFERENCES `virtual_pets` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_virtual_pet_activity_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE INDEX `idx_virtual_pet_activity_logs_user_created` ON `virtual_pet_activity_logs` (`user_id`, `created_at`);
        CREATE INDEX `idx_virtual_pet_activity_logs_pet_created` ON `virtual_pet_activity_logs` (`pet_id`, `created_at`);
        CREATE INDEX `idx_virtual_pet_activity_logs_type` ON `virtual_pet_activity_logs` (`activity_type`);
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `virtual_pet_activity_logs`;
        DROP TABLE IF EXISTS `virtual_pets`;
        """
