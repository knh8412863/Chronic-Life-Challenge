from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `user_consents` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `consent_type` VARCHAR(40) NOT NULL,
    `is_agreed` BOOL NOT NULL,
    `agreed_at` DATETIME(6),
    `withdrawn_at` DATETIME(6),
    `policy_version` VARCHAR(20) NOT NULL,
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_user_consents_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uid_user_consents_user_type` (`user_id`, `consent_type`)
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `policy_documents` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `policy_type` VARCHAR(40) NOT NULL,
    `title` VARCHAR(100) NOT NULL,
    `policy_version` VARCHAR(20) NOT NULL,
    `content` LONGTEXT NOT NULL,
    `changed_at` DATE,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    UNIQUE KEY `uid_policy_documents_type_version` (`policy_type`, `policy_version`)
) CHARACTER SET utf8mb4;
        CREATE INDEX `idx_policy_documents_type_active` ON `policy_documents` (`policy_type`, `is_active`);
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `policy_documents`;
        DROP TABLE IF EXISTS `user_consents`;
        """
