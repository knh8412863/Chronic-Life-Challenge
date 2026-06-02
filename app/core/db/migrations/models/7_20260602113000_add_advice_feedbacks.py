from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `advice_feedbacks` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `feedback_type` VARCHAR(15) NOT NULL,
    `comment` VARCHAR(500),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `advice_id` BIGINT NOT NULL UNIQUE,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_advice_f_llm_advi_advice` FOREIGN KEY (`advice_id`) REFERENCES `llm_advices` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_advice_f_users_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE INDEX `idx_advice_feedbacks_user_id` ON `advice_feedbacks` (`user_id`);
        CREATE INDEX `idx_advice_feedbacks_type` ON `advice_feedbacks` (`feedback_type`);
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `advice_feedbacks`;
        """
