from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `vital_records` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `record_date` DATE NOT NULL,
    `measured_at` DATETIME(6) NOT NULL,
    `measure_type` VARCHAR(25) NOT NULL,
    `sbp` INT,
    `dbp` INT,
    `glucose` INT,
    `memo` VARCHAR(255),
    `is_critical` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_vital_records_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE INDEX `idx_vital_records_user_date` ON `vital_records` (`user_id`, `record_date`);
        CREATE INDEX `idx_vital_records_user_measured` ON `vital_records` (`user_id`, `measured_at`);
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `vital_records`;
        """
