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
        CREATE INDEX `idx_challenge_checkins_user_date` ON `challenge_checkins` (`user_id`, `checkin_date`);
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `challenge_checkins`;
        DROP TABLE IF EXISTS `challenge_participations`;
        DROP TABLE IF EXISTS `challenges`;
        """
