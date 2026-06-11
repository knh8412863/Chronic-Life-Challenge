from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users`
            ADD COLUMN `auth_provider` VARCHAR(20) NOT NULL DEFAULT 'LOCAL',
            ADD COLUMN `google_sub` VARCHAR(128) UNIQUE;
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users`
            DROP COLUMN `google_sub`,
            DROP COLUMN `auth_provider`;
        """
