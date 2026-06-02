from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `prediction_feedback` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `feedback_type` VARCHAR(15) NOT NULL,
    `actual_diagnosis` JSON,
    `comment` VARCHAR(500),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `prediction_result_id` BIGINT NOT NULL UNIQUE,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_predicti_predicti_feedback_result` FOREIGN KEY (`prediction_result_id`) REFERENCES `prediction_results` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_predicti_users_feedback_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE INDEX `idx_prediction_feedback_user_id` ON `prediction_feedback` (`user_id`);
        CREATE INDEX `idx_prediction_feedback_type` ON `prediction_feedback` (`feedback_type`);
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `prediction_feedback`;
        """
