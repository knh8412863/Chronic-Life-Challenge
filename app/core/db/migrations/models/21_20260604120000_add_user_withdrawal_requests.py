from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `user_withdrawal_requests` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `withdrawal_reason` VARCHAR(40) NOT NULL,
    `withdrawal_comment` VARCHAR(500),
    `confirm_agreed` BOOL NOT NULL DEFAULT 0,
    `requested_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_user_withdrawal_requests_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE INDEX `idx_user_withdrawal_requests_user` ON `user_withdrawal_requests` (`user_id`);
        CREATE INDEX `idx_user_withdrawal_requests_reason` ON `user_withdrawal_requests` (`withdrawal_reason`);
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `user_withdrawal_requests`;
        """
