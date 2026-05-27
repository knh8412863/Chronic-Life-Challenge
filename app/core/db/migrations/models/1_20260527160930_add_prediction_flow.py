from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `chronic_health_inputs` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `age` INT NOT NULL,
    `gender` VARCHAR(6) NOT NULL COMMENT 'MALE: MALE\nFEMALE: FEMALE',
    `height` DECIMAL(5,2) NOT NULL,
    `weight` DECIMAL(5,2) NOT NULL,
    `bmi` DECIMAL(5,2) NOT NULL,
    `sbp` INT,
    `dbp` INT,
    `glucose_fasting` INT,
    `diagnosed_diseases` JSON NOT NULL,
    `medications` JSON NOT NULL,
    `last_checkup_period` VARCHAR(20),
    `fh_diabetes_father` BOOL NOT NULL DEFAULT 0,
    `fh_diabetes_mother` BOOL NOT NULL DEFAULT 0,
    `fh_diabetes_sibling` BOOL NOT NULL DEFAULT 0,
    `fh_hypertension_father` BOOL NOT NULL DEFAULT 0,
    `fh_hypertension_mother` BOOL NOT NULL DEFAULT 0,
    `fh_hypertension_sibling` BOOL NOT NULL DEFAULT 0,
    `family_history_ckd` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_chronic__users_9e562357` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `lifestyle_inputs` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `smoking_status` INT NOT NULL,
    `alcohol_frequency` INT NOT NULL,
    `alcohol_amount` INT,
    `walking_days` INT,
    `sedentary_hours` DECIMAL(4,1),
    `exercise_frequency` INT NOT NULL,
    `physical_activity_min` INT,
    `sleep_hours` DECIMAL(3,1),
    `stress_level` INT,
    `diet_score` DECIMAL(3,1),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_lifestyl_users_7efbdb40` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `lipid_obesity_records` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `record_date` DATE NOT NULL,
    `total_cholesterol` INT,
    `hdl_cholesterol` INT,
    `ldl_cholesterol` INT,
    `triglycerides` INT,
    `height_cm` DECIMAL(5,2),
    `weight_kg` DECIMAL(5,2),
    `bmi` DECIMAL(5,2),
    `waist_circumference` DECIMAL(5,2),
    `memo` VARCHAR(255),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_lipid_ob_users_ac14f404` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `renal_records` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `record_date` DATE NOT NULL,
    `creatinine` DECIMAL(5,2),
    `egfr` DECIMAL(6,2),
    `bun` DECIMAL(5,2),
    `urine_protein_pos` BOOL,
    `memo` VARCHAR(255),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_renal_re_users_8648bfa7` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `prediction_input_snapshots` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `input_mode` VARCHAR(10) NOT NULL,
    `used_default_values` BOOL NOT NULL DEFAULT 0,
    `missing_fields` JSON NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `chronic_health_input_id` BIGINT NOT NULL,
    `lifestyle_input_id` BIGINT NOT NULL,
    `lipid_obesity_record_id` BIGINT,
    `renal_record_id` BIGINT,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_predicti_chronic__b84bc528` FOREIGN KEY (`chronic_health_input_id`) REFERENCES `chronic_health_inputs` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_predicti_lifestyl_90639d5d` FOREIGN KEY (`lifestyle_input_id`) REFERENCES `lifestyle_inputs` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_predicti_lipid_ob_d965cb20` FOREIGN KEY (`lipid_obesity_record_id`) REFERENCES `lipid_obesity_records` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_predicti_renal_re_9ad4a628` FOREIGN KEY (`renal_record_id`) REFERENCES `renal_records` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_predicti_users_75c82619` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `prediction_tasks` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `task_uuid` VARCHAR(36) NOT NULL UNIQUE,
    `prediction_mode` VARCHAR(9) NOT NULL COMMENT 'SCREENING: SCREENING' DEFAULT 'SCREENING',
    `status` VARCHAR(7) NOT NULL COMMENT 'PENDING: PENDING\nRUNNING: RUNNING\nSUCCESS: SUCCESS\nFAILED: FAILED' DEFAULT 'PENDING',
    `requested_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `started_at` DATETIME(6),
    `completed_at` DATETIME(6),
    `error_message` VARCHAR(500),
    `input_snapshot_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_predicti_predicti_fe8af586` FOREIGN KEY (`input_snapshot_id`) REFERENCES `prediction_input_snapshots` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_predicti_users_e48402e4` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `prediction_results` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `overall_risk_level` VARCHAR(10) NOT NULL,
    `lifestyle_priority` JSON NOT NULL,
    `input_completeness` JSON NOT NULL,
    `inference_ms` INT,
    `disclaimer` VARCHAR(500) NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    `task_id` BIGINT NOT NULL UNIQUE,
    CONSTRAINT `fk_predicti_users_df8e9b26` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_predicti_predicti_2e9db6ee` FOREIGN KEY (`task_id`) REFERENCES `prediction_tasks` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `prediction_result_items` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `disease_code` VARCHAR(30) NOT NULL,
    `model_version` VARCHAR(20) NOT NULL DEFAULT 'V8',
    `probability` DECIMAL(7,6) NOT NULL,
    `threshold` DECIMAL(6,5) NOT NULL,
    `threshold_profile` VARCHAR(15) NOT NULL DEFAULT 'SCREENING',
    `is_at_risk` BOOL NOT NULL,
    `risk_level` VARCHAR(10) NOT NULL,
    `message` VARCHAR(500) NOT NULL,
    `result_id` BIGINT NOT NULL,
    UNIQUE KEY `uid_prediction__result__14a614` (`result_id`, `disease_code`),
    CONSTRAINT `fk_predicti_predicti_ae9656ed` FOREIGN KEY (`result_id`) REFERENCES `prediction_results` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `user_profiles` (
    `birth_date` DATE NOT NULL,
    `gender` VARCHAR(6) NOT NULL COMMENT 'MALE: MALE\nFEMALE: FEMALE',
    `height_cm` DECIMAL(5,2) NOT NULL,
    `weight_kg` DECIMAL(5,2) NOT NULL,
    `bmi` DECIMAL(5,2) NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL PRIMARY KEY,
    CONSTRAINT `fk_user_pro_users_f50f74ad` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `prediction_result_items`;
        DROP TABLE IF EXISTS `prediction_results`;
        DROP TABLE IF EXISTS `prediction_tasks`;
        DROP TABLE IF EXISTS `prediction_input_snapshots`;
        DROP TABLE IF EXISTS `lipid_obesity_records`;
        DROP TABLE IF EXISTS `renal_records`;
        DROP TABLE IF EXISTS `lifestyle_inputs`;
        DROP TABLE IF EXISTS `chronic_health_inputs`;
        DROP TABLE IF EXISTS `user_profiles`;"""


MODELS_STATE = (
    "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"
)
