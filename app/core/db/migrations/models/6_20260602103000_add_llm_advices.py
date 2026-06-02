from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `llm_advices` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `advice_date` DATE NOT NULL,
    `context_snapshot` JSON NOT NULL,
    `prompt_summary` LONGTEXT,
    `advice_text` VARCHAR(400) NOT NULL,
    `provider` VARCHAR(20) NOT NULL,
    `model_name` VARCHAR(50) NOT NULL,
    `input_tokens` INT,
    `output_tokens` INT,
    `cache_read_tokens` INT,
    `trigger_type` VARCHAR(10) NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_llm_advices_users_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE INDEX `idx_llm_advices_user_date` ON `llm_advices` (`user_id`, `advice_date`);
        CREATE INDEX `idx_llm_advices_trigger_type` ON `llm_advices` (`trigger_type`);
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `llm_advices`;
        """
