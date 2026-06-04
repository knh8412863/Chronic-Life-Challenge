from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `notification_preferences` (
    `user_id` BIGINT NOT NULL PRIMARY KEY,
    `push_enabled` BOOL NOT NULL DEFAULT 1,
    `health_data_reminder_enabled` BOOL NOT NULL DEFAULT 1,
    `challenge_mission_enabled` BOOL NOT NULL DEFAULT 1,
    `prediction_result_enabled` BOOL NOT NULL DEFAULT 1,
    `advice_update_enabled` BOOL NOT NULL DEFAULT 1,
    `virtual_pet_enabled` BOOL NOT NULL DEFAULT 1,
    `email_enabled` BOOL NOT NULL DEFAULT 0,
    `weekly_report_enabled` BOOL NOT NULL DEFAULT 1,
    `important_notice_enabled` BOOL NOT NULL DEFAULT 1,
    `promotion_enabled` BOOL NOT NULL DEFAULT 0,
    `quiet_start_time` TIME NOT NULL DEFAULT '09:00:00',
    `quiet_end_time` TIME NOT NULL DEFAULT '21:00:00',
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT `fk_notification_preferences_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `notification_preferences`;
        """
