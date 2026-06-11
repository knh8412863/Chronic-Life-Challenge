from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `challenges` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `title` VARCHAR(100) NOT NULL,
    `description` VARCHAR(500) NOT NULL,
    `category` VARCHAR(30) NOT NULL,
    `target_metric` VARCHAR(30) NOT NULL,
    `goal_value` INT NOT NULL,
    `duration_days` INT NOT NULL,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `challenge_participations` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `start_date` DATE NOT NULL,
    `end_date` DATE NOT NULL,
    `status` VARCHAR(15) NOT NULL,
    `progress_count` INT NOT NULL DEFAULT 0,
    `completed_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `challenge_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_challenge_participations_challenge` FOREIGN KEY (`challenge_id`) REFERENCES `challenges` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_challenge_participations_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `challenge_checkins` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `checkin_date` DATE NOT NULL,
    `note` VARCHAR(255),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `participation_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_challenge_checkins_participation` FOREIGN KEY (`participation_id`) REFERENCES `challenge_participations` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_challenge_checkins_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uid_challenge_checkins_daily` (`participation_id`, `checkin_date`)
) CHARACTER SET utf8mb4;
        CREATE INDEX `idx_challenges_active` ON `challenges` (`is_active`);
        CREATE INDEX `idx_challenge_participations_user_status` ON `challenge_participations` (`user_id`, `status`);
        CREATE INDEX `idx_challenge_checkins_user_date` ON `challenge_checkins` (`user_id`, `checkin_date`);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `challenge_checkins`;
        DROP TABLE IF EXISTS `challenge_participations`;
        DROP TABLE IF EXISTS `challenges`;"""


MODELS_STATE = (
    "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"
    "Tl/z9/8D5IAhEA=="
)
