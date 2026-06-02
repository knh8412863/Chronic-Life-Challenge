from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `notifications` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `notification_type` VARCHAR(20) NOT NULL,
    `title` VARCHAR(100) NOT NULL,
    `message` VARCHAR(500) NOT NULL,
    `link_url` VARCHAR(255),
    `is_read` BOOL NOT NULL DEFAULT 0,
    `read_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_notifications_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE INDEX `idx_notifications_user_read` ON `notifications` (`user_id`, `is_read`);
        CREATE INDEX `idx_notifications_user_created` ON `notifications` (`user_id`, `created_at`);
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `notifications`;
        """
