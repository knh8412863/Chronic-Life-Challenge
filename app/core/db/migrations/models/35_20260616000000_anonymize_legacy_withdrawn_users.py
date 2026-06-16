from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        UPDATE `users`
        SET
            `email` = CONCAT('withdrawn_', `id`, '@all4health.deleted'),
            `phone_number` = RIGHT(CONCAT('WD', LPAD(`id`, 9, '0')), 11),
            `google_sub` = NULL,
            `profile_image_url` = NULL
        WHERE `is_active` = 0
          AND `email` NOT LIKE 'withdrawn\\_%@all4health.deleted';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return ""
