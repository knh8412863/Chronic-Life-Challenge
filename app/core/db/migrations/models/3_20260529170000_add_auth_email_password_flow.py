from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users` ADD `is_email_verified` BOOL NOT NULL DEFAULT 0;
        CREATE TABLE IF NOT EXISTS `email_verifications` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `token_hash` VARCHAR(64) NOT NULL UNIQUE,
    `expires_at` DATETIME(6) NOT NULL,
    `verified_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_email_ve_users_1f4af20f` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `password_reset_tokens` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `token_hash` VARCHAR(64) NOT NULL UNIQUE,
    `expires_at` DATETIME(6) NOT NULL,
    `used_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_password_users_42361ab8` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE INDEX `idx_email_verif_user_id_f8a483` ON `email_verifications` (`user_id`);
        CREATE INDEX `idx_password_re_user_id_5a5db6` ON `password_reset_tokens` (`user_id`);
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `password_reset_tokens`;
        DROP TABLE IF EXISTS `email_verifications`;
        ALTER TABLE `users` DROP COLUMN `is_email_verified`;
        """
