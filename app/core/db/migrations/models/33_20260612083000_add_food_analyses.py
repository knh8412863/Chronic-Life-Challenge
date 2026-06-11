from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `food_analyses` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `meal_type` VARCHAR(20),
    `image_s3_key` VARCHAR(500) NOT NULL,
    `task_uuid` VARCHAR(36) NOT NULL UNIQUE,
    `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    `requested_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `completed_at` DATETIME(6),
    `error_message` VARCHAR(500),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_food_analyses_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE INDEX `idx_food_analyses_user_requested` ON `food_analyses` (`user_id`, `requested_at`);
        CREATE INDEX `idx_food_analyses_status` ON `food_analyses` (`status`);

        INSERT INTO `food_analyses` (
            `user_id`,
            `meal_type`,
            `image_s3_key`,
            `task_uuid`,
            `status`,
            `requested_at`,
            `completed_at`,
            `created_at`
        )
        SELECT
            `user_id`,
            `meal_type`,
            CONCAT('legacy-food-analyses/', `task_uuid`, '.json'),
            `task_uuid`,
            `status`,
            `created_at`,
            CASE WHEN `status` = 'SUCCESS' THEN `created_at` ELSE NULL END,
            `created_at`
        FROM `food_analysis_results`
        WHERE NOT EXISTS (
            SELECT 1
            FROM `food_analyses`
            WHERE `food_analyses`.`task_uuid` = `food_analysis_results`.`task_uuid`
        );

        ALTER TABLE `food_analysis_results`
            ADD COLUMN `food_analysis_id` BIGINT UNIQUE;
        UPDATE `food_analysis_results`
            INNER JOIN `food_analyses`
                ON `food_analyses`.`task_uuid` = `food_analysis_results`.`task_uuid`
            SET `food_analysis_results`.`food_analysis_id` = `food_analyses`.`id`;
        ALTER TABLE `food_analysis_results`
            ADD CONSTRAINT `fk_food_analysis_results_analysis`
            FOREIGN KEY (`food_analysis_id`) REFERENCES `food_analyses` (`id`) ON DELETE CASCADE;
        """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `food_analysis_results` DROP FOREIGN KEY `fk_food_analysis_results_analysis`;
        ALTER TABLE `food_analysis_results` DROP COLUMN `food_analysis_id`;
        DROP TABLE IF EXISTS `food_analyses`;
        """


MODELS_STATE = (
    "eJztXftz4riW/lcofppbxU51nt2T2toqktDduUNIKqH7zt3OlMsYBbTxg+tH0tm987+v5AfYsmQsY8AyZ2qqA1hH"
    "4E+ydM53Hvq/ruVMken92kcuNubdi87/dW3dQuQFc6XX6eqLxepz+oGvT8ywqb5qM/F8Vzd88umzbnqIfDRFnuHi"
    "hY8dm3xqB6ZJP3QM0hDbs9VHgY3/FSDNd2bInyOXXPjxJ/kY21P0E3nJ28WL9oyROc38VDyl3x1+rvnvi/CzG9v/"
    "HDak3zbRDMcMLHvVePHuzx172RrbPv10hmzk6j6i3ftuQH8+/XXxfSZ3FP3SVZPoJ6ZkpuhZD0w/dbslMTAcm+JH"
    "fo0X3uCMfst/HB+dfjz9dHJ++ok0CX/J8pOPf0W3t7r3SDBEYDTu/hVe1309ahHCuMLtFbke/Uk58K7mustHLyXC"
    "QEh+OAthAlgRhskHKxBXE6cmFC39p2Yie+bTCX58dlaA2ff+w9XX/sMvpNXf6N04ZDJHc3wUXzqOrlFgV0DSR0MC"
    "xLi5mgAeffhQAkDSSghgeC0LIPlGH0XPYBbEvz/ejfggpkQYIKfY8Dv/7pjYyz3UzQC0AD96v/RHW573LzMN2y+3"
    "/T9YRK+Gd5fh/TueP3PDXsIOLgm6dLF8fkk99vSDiW68vOnuVMtdcY4dUdv8JevYYj/RbX0WYkXvmN5fvH1cYw/p"
    "Hroi73i7S/py4RYzjRqS8SeY72+nMeIfWvZJT9rX86hvfb/JPOgnZZ7zE/FjfhI/5eL9hwzqwtTftfC9BKqsnJoL"
    "6VkZfM/E+J7lVtH0z5KBMytWCc14JrZrW8eeRlYY/MqZnJeOYyLdFqiYaTkGzgkR3NbsXC4Hde9Kl3d3w8yudHkz"
    "ZnD8dns5INt+CC9phP1IC4910NQK6iJ615rO2eyvyRUfW0iwlmYk2T0/Fv01edHQFYDcw/TONt/j0SrAfHxzO3gc"
    "92/vM8Bf98cDeuU4/PSd+fSXc2Z6Lzvp/ONm/LVD33b++240YLWGZbvxf3fpb9ID39Fs503Tp6l9Jvk0AaYpSsbA"
    "0rH5nRihz9jQ4yHJqRr5RoUKB6LNtddU+z2qHTwD9xLPWmTj/nZ8fHLy8fjDyfmns9OPH88+fVgau/lLRVbv5c0X"
    "uuhknoL1lrDvvCBbm+veXGbjzEqpqOOdn5bYNc9PhZsmvZRd39HPBSaLSoX1PSup5vquyHqe3HZuQU+PZLT2Vdqq"
    "GdEaxnL3+mWbhhKUrhYpXemBDTzkarLaQUpovYrQkCHcmZaQU2mzYOeR/uy4CM/s39F7iPYN+d26bfBMv1gR/RZ3"
    "0zyU/0pmSvLpaha6+ttSL01PIHJ75KZQZO1d9R+v+teD7l/7MQPudc97c9zpA/KQP6a6WZdjB3BaFRoCi7i95lIB"
    "LdT5wBQAUwBMgS6YAgeiP5IFv4rymBIDEwBMADABwARQQTsAE0BdE8AxsfF+7RiBhcLfnlf/sy2KVf+wrTaNG29B"
    "6/+RfEc4QXrLr0zCrP4Es6AhZgEzTnm7YGAHVu7xz2DODvV+oxa647vHiw7558m+f7j53r/650UnfvFkfx30h+Ov"
    "Gtnf+hed1Jsn+7b/8DvZ80ZfLjrLl0/28O6qP765G110klfdCibIaZmIiFNxRMRpLiLCx74pFVqyFFAzpmQrwXnM"
    "miSBZl5STViPy6B6LAb1uHzA4xj9FCzZ4oDHxqJYpGYP/hhnNOxcoONSyx7ejb4kzdnoRwbVuW7PCowcAbAZqSID"
    "RzUrldonENMEMU3bXSrbZVs3JKYpNBE59ktiOoqtFmqagYOivZZIGJkmo4UtBVRRG7ZtFVA3DVl0E8+eDJYcUTVR"
    "PTr+VMZSOP4kthTotSywsoH8agfw128VkDue8gjGcvzCSnrf1MJtfzig/MBw8GR/HkTvor9VaIHzMo5JsV+SBXmC"
    "XX8+1d9lTIS0zIYGQrPMMI6FsCB3hzQy2yaiqSgw9hk5NR/qo6Myy+KReFU8ytEnrvOMTaRhi2h6WuBK7d1cYSUz"
    "dM5KUVNnBdTUWZ6aItr7XCMYvWLhusnHNSe4u9napRRpaHo2dRdynBmZcl4wkUE0K1XLFN1tAMxWNCKgW+qnWwg2"
    "6ewcxDM412Cbl98hxrLG+L5A1qcW5tD9a+dtIgaQZiE1dc/XTGfGA7WYJsxKQiwVxFIB37uVWKrFtOLAZiVhYPc6"
    "sOGPl+DxGW41n/XLbIBxJ59/f0DmMpWYH+nFzTpu3tCLwr6yhqwoE6I6PPxkDEXxoVeTMLHqkFAHz1XUk8JYxH4t"
    "Lanb4zpvNeByG/UaVw1SGJ437M+nrv6mm+RhIr/Mq2PW/GPZ6UPUp8IAPTsO2Uxt3Xz30IbQfCZd9cOesNcORIiR"
    "RZZg8s01IvMQdqgwPiFdgv13aidtiEs/7mrozBQGxJi7jo0NbY50059r2F4Em06Yq6jLr2GPN7RDhfEh3+0aZCep"
    "YcIM4q7UnjAmfiabxjv1NtQwV4ZJb6rPExMv8FRzJsijq4uLDKKvbowN6fIu6vEh7FBhfCyyGtTwDN2SbtR+fhYu"
    "oqVHSdfaM0JTamtuah4te/wcd9gOeML1RfNsfeHNnU0XmhVI4UrzGPfaDqRq0fNWCCmv5aWg8XWvvudrTDpTGBYX"
    "2aEpWcPe9EC7Un5TIup7XYB8p10pD4g+fcUGqmtj6oe9tWBTMk1Li6DZVKUb3kagKAyGMddNGg6BNGOOjBe8Kbt7"
    "lfR3FXXXCmhMpE+RO3H0jReWJTzDVZetgGihuz428KIOB8oSpPt0p62AaaJPZ5suO5T3vaT9KIyI7fh1udtGqa4U"
    "RiTM/UA/F467qep/TXoahB0pDMcbQi8mpV5qAOQfYV8PSHFIXrHrB0TDXSBfq5H5/h51e4/8dnDgUx2TiRMz4B5R"
    "4Tddb69phxH//Ui7UxgbFz0TOOaRH1/zkOdtvv4+RH2GnvzHqEeFEfKQEbj0wdKDKfZreLwe4w77tL9yT9beIvXy"
    "0Eilu6Ydc4YT2L7m+XrR4n1no7FD/imn8/SjTh+TPtVBkeeiS6IkZo7OyQ6phlDsq4tjJb7EPauJ08ozVSdCSw+V"
    "2uDEKUJ1oXK/6k5NPNLmhLYguxxyUZwuuSk+afPiPtOzmlCltMg64Flpj2pBUqE0Q2b/EZRpYPeo4pINWm6f3E/9"
    "hmbUkzyMUg4Wosmy3hwvtJmryx0tyJPdYRLjU2B8/Gg8BRPj6FPnKZiefyJvjPPph+4Gg7KV8wfThcwwNzxXOK1X"
    "Arurkvph40m94XnBKbULvSKOtiWEa9l+d2gdNQctSB45yOSRvFW8rlxwolDlqnnUWyx421uoSJ3qbVQqeOOiWUnu"
    "hEApS6VWrNHH0ukcdVf9TSZG/B3RkEOx36boZZlh4epk66vxsH3suybPIZT7pdnnZOGvUhFgJbfDtPVaFuAtZ61H"
    "wFTQajKCkLO+55z1JOPMrjCSrCwM5p4HEypy11/1CMy39phvUKyjdeOaXwSbQVTvYAjh4KM9Ood6ahx8xKmOICBA"
    "8jUU1vAgTCmHrfIhSSCEQX4L8CGN4UMywyKhbbJyauqa9TuisKctXGzpLqcI8TqiIiUIBfbgHA5Q9UDVA1Xv0FS9"
    "fKkngbbHrQm1RuETFKeC42RaqdtlRlv3RHTieocXt6N9e71Gd2Pt2+Pg87fhRWf1eukD067uRleDh9HSF5Z88GQT"
    "1e1aG99RiYtO6s2T/fnu2+ha6w/HpF1/fPOdHm7BfvRk342/Dh4uOuGfZnjHUgNkOJbFPX5QrMvzpeEogpTP+Bm7"
    "VjUHZF4YdPssvPFOVEm7Z2VBvwf9HvR70O+bqd9n6pVy1Hq2nqlYm88VUd2qCv8jDWhmySUNf3RpWkPgRaQuaPr7"
    "yTYgups4pE2UZpASUlLbqz9UIDqMyzvRXhCHwBVjycqpSYdvRXumxdy0IOCtAWI8M0L1gLnbI6dOyhxteCI+2/Ak"
    "d7hhvMpyQVxvwq+kd5hJdD8YXd+MvnRzoCZXiHEevXiyH76NRuEn8Ysn+/Hb1dXg8fGiE78g5nn/Zji4JjZ5+LeK"
    "6V209Caj8lE4KB/ZMQHTpcWmi+FYC6o4VvI6MbIQV7nnuErkuo6rWcjz9JmUlpQTVFJT2g4vBk7Zdq58QNr0gLRp"
    "LWmTVt+SmtnMNJeuj1HpvBV162RwbncNnbUCpRSplT0HB/zTrWStgBk4WGYgNunbywyE5CpVYPmqcQEjmwgVacVN"
    "3lx4AFKllgcQUNabU9bhrhm+kQAyI6QmWX1UyqQ9KjBpj/ImrW7RQl0ySK4klJyPZ+V4gQJaIMcK6KbjYl41XqHm"
    "lBapZDvuAcWaSwwZujvxtBlnt0AGtnRTBNxSit0uIrFfY/FGYli0YQyubm77w1/Oe8dM/FA6Po6pAeY6PsK2NIgZ"
    "OYDxWfelIVzKAHyeM8WBpVmyEGbk2gnjJxkYg5nuSs/DlFQ7IZR6kPEEyUOYkgII08cLSOgzrJhifHhtSo2LvRft"
    "2dR5xfX//ng3EjjGM1LsJMSG3/l3x8TbOwO9+5/PgR0eHdiZBNj0se39Sr/vv/JsRR3zkgKR8QslyvUvt/0/WL37"
    "anh3yTp8aAeXrB0TnQnno59yxkxWTE3DEHyd4OuU8HVCcaA2DGyuOBD4sHu1u3IY0nHpqpOFmSddC+/THr8ZBAxs"
    "NWBgj2fcN8zrL4qNyDyjeWwkK12zmS0Ne67LzjjewrXtytfp4/o4QRbMaX7i6IrcWYLbqvQUHc0d+TGh0FNTgi3S"
    "o8JVdEVR6hmxDZ3S+9tMSnqlddNw5o6pPYfR+bbBSQISTkmu7IG6sxIsRP7UtSAK3aqHguCbbr6Q7yNP3ruMK5UV"
    "O1D0PDRFtq+779rcCVwOgMVuhLx0O7nw0x5bnqHAI2MitKgGZ1aynVCeyEDpu8jzNNlDmFixA322pxj5IpdM4TzM"
    "CsI0tJDlyHgHkvZKBjodn52Vibw7OxOH3tFr4BVoIXkMXoGWDix4BYCoVpuo3mY5ovgc+a9htMqNvQi4WVycVr0i"
    "ntGI2mtxEAymEpDF1V5ikZtPL+Z3uEn0TV9Ha7NdyB1OeYtiuVStlfS+i68SU2NAzw0c0qKpg+hd9LdbQTcvkxEn"
    "TojL5cPNyf4y5yluRcbhSmhjw7BhLHdsGZ5JxD2+VUHwDRBcITixsCR8sQRg133TsedrBnaNwHpGLoqXQpmpyO+h"
    "nZSPDLTeZCFDOEatD5VnlMJqetBYzczAcDykPeueT7+3PG4cyQPFcIr1mU2gyJ7HVTZqni8N0fNVouctRIAKA76k"
    "hoARA+yrYG/qdOeeI+MlWGgL5GJHqjyIQFxNl0X9tQLmZHXQJ8hHHllwQyolh23haQb8DuBEAzHMlrMhzKsOAGYx"
    "zB6emFzFozTOqR4A6BzQc9K36yObni1eeekQdAJwF8NddQkRdAJwF8NdeSkR9QKAsxUmLGy+a3OimTruu2a8yJ6p"
    "xO8AYIbglBbGMHCCUyCIAYIYVApiSPHPtr7w5o6/YbbdvUupFtomDEh4jHtVC2BO+l19sR2Dn8g1sIcEWWPpy72i"
    "aA4UN9xS1hhEcTQkimM5zrIJYjnBtqeILW84vMMcUgUnSbCCqpZXKVVdRaJi5DRww/Ves7Ad+FKVI3miiqk3NZaQ"
    "jKpoapPAtRFnwVxbfzMleaA+OEiJyD3KkBIBViftAlIiWjGwkBIBbILabMI2zeYhfkae/24iYToE06JXZDybSVvI"
    "gmi7/exZTlh3QXQWizjGMieo2IJae82Q/dZeaRGQUHwFiq/sAz0ovlJ78ZUld1hlceQLH+rquJi/e9jQySqXFMSz"
    "sC2BplD+UJ92qAtU9JRDXaDd5U9AXaBapiFQuK1g+iBwCKg+xak+CBzaeeDQEC/w9G6CPKLZPoTFf7tcFjTXqlfM"
    "hJL2mhMJaFFRYaBD20uHQrXpMqFEvuMTO9KYOybyfOQ6Mko/V/ZANf/5tCqKHMkDxdCsjCFH8kAxJN82M98N5OKp"
    "VBRbTu5A8YtqMGmGJWnAZ+Taab/LV2/SXmSP/szIAYz7K+GkPHRQwWlr0EKE6hI+iFAFehMiVFs3sBChCrQ10NY1"
    "0daNPm2yPtY6OX6TQ1WnTuYU89OZU0CBk24lJx2OsSwjnRFqOx8d3qxsWmtGSM2U1i0U2qMHxYZvJJDMCKmJ5NGH"
    "MlCSVkIsw2tMPLMgjlmMpDCAWQ2zt/4U6yTDV4KUToscKB9t6O7E02Rp1JRUO+mqcwm6auE6PsK2NIgZOYDxWfel"
    "IVzKAHyeM8WBpVmyEGbk2gnjJxkYg5nuSs/DlFQ7IZR6kPEEyUOYkgIIwQOS0wXBA3KIRDl4QFo6sDkPSMgM6LZu"
    "vnvY00i3BC5pj0hBJ2rZdzvhEcH9BO6nRruf1q0PNaD4mXTbj3t9WHbauGWhLKQFC2AG4sfBuDP6NhzuqwjNLf3z"
    "HblehEPeo5W+3it0a9GPtNeo6RZ8Wz+6r6ufEZ87RcZhGs6p6Mt93Xvp/sk4wX7kGpMBCfOpUdQWPGT78JClBrOs"
    "cZUSUdNjUb/vh53aZaFk5dTE86QMnidiPE/y9v5qHZFAMyu1OyzJozfqP/xTuxr2Hx9vPt9c9cc30TFpDYXXn5Od"
    "cO6YnMW1kJPKyLWVlTorzUqtNrD8HlV0lklGbodHmCw3sAafYGIhX6ebVR7SokMYVzLNOIGRfq1KJzACO9gKEili"
    "B3OmdpmoxcUy3HBpJfnIqi2GMTIlb0iXTd4YdhvAuELnM0JT2meXY/lxWvWK7L/UQD6nBSDAsY3mWzLE0iF8OUE1"
    "TY+jMq6yI7Gn7CjnKCPPSEDjP6OztbHUadA82Y0UkkapyNvRPBzLQnKRfikRJf27Z6UCJs8KAibP8gGToMG1SIMD"
    "V9SuHH0ctVcSalEP9eDeHi0GHIA7PiGhYJLnwb6z0dgh/5SEmjXsmji1y4IueoBLjEBN5l82wa/QBszlApYyBMOj"
    "KLRMYiLYg8qupL0CezAaaUvSDZWVUtQSLJeFVJCExKrUZDWeavGP1V51M+Dl0hQS/YIe4NRyhvPHnkfPUIgndA7j"
    "AuY/J9kM/p9+H/D/YD3u3Xo05q5jY0ObI93057EiILsLF3QC1mWRdckcBiYNPF8eMC/GPF92uALwwk4gbroAfBfZ"
    "ulkVdI4wgA1B6sBR7QTlrQSp8zSHGlC8irr9Gva6PJRTXUwLFKz1GDNKQg3w5s87VRdavgpVBtW8BlALtLxDFBq3"
    "oZVHV6gnrYc4vd/XAO0D7a4FmHLUoOrF6GgwdG1BXOM4slqd1WBH8VuxE6SQuV85SkpR9pErAqj69lL1zivBxCRP"
    "OvZeROf/iSl7vjRQ96xOtHCx45LNSYZV5ksDs1yFWY60LsOxFnT/spEnxe/zpZsxEqrF+GM7Lqqv8cK6xes6I6YW"
    "JVPjSaOeYerY4rEAhfl9KSk1V2cIVwSHE4QrNoPypeacNLopIQhKBMJ3L0Xx95dM1iBkOWxE9tHOA1Q5LrMqV9OU"
    "qMzUoiUdiJlPjxLPvARgmfmXTsRrnOJbOPk2YLfCx60Ew5U8lhIs1yrVtO5SNatw50ylDbY2DZBg+yLBoHDKWsuq"
    "QuGUCkV9coI7LJ/y/dMGNMq2S/ssXGeiT7DJ5RDX1TNPS25cL2V/mgwPzKRgysfeeemCKc2oO9NMHGUKzyzx0Mgc"
    "e8am1NLJFd7h0/549TAYjG5GX2p76OtPAqcVevzQt8LZ/9eV9lkJ7jDQf2vzs8Y4/2qeLvBw8TxcFvI8orhLbfEr"
    "ETVR3AoTHU6vZ2JzOK6Ua4qVa4ZTSjX3YEbtJObgszS7KepBLT/VzuO0K+W6byHBvU0IF7DJtdVnriPzujnccomE"
    "68LVogZA2crKjVshymIpWggbVeeaIagL+cSEwi7FJC4DHSFarpVEYegPCAIezgWmblqoHp1362hnCcLzMgQh6+5P"
    "EYTneTpr+ciIqwQM7MDKLZ+iqje7LxtQRCGsrl10ss0kof+tBPK/CYH/LXeOmq/7AcfAKAf3SnqHKN8PRtd8jOMr"
    "F534xZP98G0UYR6/eLIfv11dDR4fyShEL57sz/2b4eD6ohP9rTImRctKMiYfhWPykUPtUtvE0xbINbhF6AqqPuVF"
    "d6cQf9h4Na/vvNTAdcn9a56PFjJLMyunZCW/rRx97CJyM1614DhWFsLjGhYeRxZyt9rQZiVrGNhG1RZt0jgmt11c"
    "WCOOSa8UwsrIwmDueTCR6zquVoFSzwkquY1thVfP1pyTphq54kA5Qj2IhhC6EB5cNjxYvCjUSofnKmOqCyl37du8"
    "IGypiFmRo2KTeFkFz5GUjZZNFx/gkNpMbQIxo51O/gc6u710dlzegWr4fOtBZN9nxIoMh0YvgdxAOGIJ8LIEsY1t"
    "HkhFAYNZwXaeVHfWOy4dMIhmzxxtpRDCRKSd4J1LgDcJOJHUhdjFEu2ETmbeBeTLaBUFx0fY1ojZztlWCgso8+Sr"
    "RVU2CstaD0y0HBnKImmvJFNxfFYm1Je0Egf4n+WCfSEXvaVke7CYVhzYrCQM7F4HNv7xQHQB0dVooqtMHnzmDBY+"
    "wyKXCy9LezWMYtlWnCGdbnGV2OsoVfSLo5tdDjUjaNkrYmnCqZAUbU1SUWdEbI+UTTMWxcNgb3zdJQOkee+e75hk"
    "Ckw4oS8F5Vh4wmqlK9QWPhSDMcX6BlCy0oeN5TMBg56JMzMDw/E4zNk6ODkdHDaiVHtduLpN5plZHVZRL4eN7Xyi"
    "HxmS9Bor2k6e7VSCZ4sRMacmUUsck4YAug4ny3bdHOV0cODTc1NEOR0cNqLkS2fmu4FcPOWdp7cOz5z4YaM5sXC1"
    "xTMWbOfSKeOiiPF4Q3g297WXWTU4M+IAaoxKBbcjI9lOKGW8j+CdaAWJDd6Jlg7sksrMRd/JH9TO59ola4BWZdqb"
    "UvlTjmffmCVeHnZVRBBnG/XWcsOrEySAFd7B1GoWK+yjRQXDZim2O+/k0Qfy38ao123SvJG7dDWrgq2dltwdisdN"
    "BJH8WtfAHtIsbAd+FUOb18PuQD1pHqSeidBCmzsBr05YGZuG6aCdps1Jjw1ZW2slTjEFx3Bc2ShfrjzAChZjKwwL"
    "sBhbOrBgMaptMd7HZZMFtuL9qqryGisxrr8M5uFBmIcT7Ppz6YyvrFTbE77I75+KTthbXyVrJb3n+sZdorINLjr0"
    "3yf78yB6F/3tlpuxmayHMkXgxDXgciXg5pGvyrAk1e2MXEur8Ms4uaq6DOv1FaqPo7wPuy7ntfrYga3XCpMAbL2W"
    "DizYeuraet+xX1TTI325V2TrvdKGUNOj9QYe1PQoY+JZSPcCt9LOxoiqubUpspUlt12opMQDEg1BbjCLahBk5dQ8"
    "jui4XC2CglIEuSLhUtlP3kFnO02lsJoeNFbyOUuQnwR1VThrmVRdFexp5Jf52NA5sTzrTlFMS+7wGEVZfXwvJX+A"
    "9GkFNwCkT0sHFgrWQMEatQvW5GnI+mi1/vQVG+gzQlPaX5fDrDEtekXkmh621Z7jxsCvtZdfS8ZYmm7ICarJN9R/"
    "zLnhWBb33KuCc5tWIkpaOls56wIU8lbobRyFHBS3LR5YEu/dsvhmxCACERTjvSrG7HTe2EM/HN72lz01bSKXhTjz"
    "jG7bUb9CjGNMZOAU2xGmaWnRjwYTQu0VsMiEiKelrIueEWu7i54I++hn0TlNf3+8G4nsg7wsixc2/M6/Oyb2GqoN"
    "FaBFbzyjuyZ2wS+3/T9Yk+FqeHfJKqW0g8v8OcTWgkAWWJbuvufRHhNA+WjnJRUxyopshMEf42KIlybC8G70JWnO"
    "4s5VNenUlLF2GTE1eYPTUibvaYHJe5o3ecnMe8XCXA3hbF3KqAnlcRkkj8VAHudwDFURLXwngWRWSk0sz8oRMQU8"
    "DP/IUd95QbZMwQNW7EADHpzArwRfTu5A8TN0Y440yoXJY8iVPVAcaYXPGTHQZVl+Vk7NVfGozKp4JF4Vj4CcBnIa"
    "yGkgT5UgTws4wLzflzPRpQ8lzocWNG4/FQ2E7JHEZKc06bbCZUVXF3tFrKiRNANStL2kqI99U07TSgRUVbHK6VhF"
    "SlZOy0r/MgkoGTE1Ad1OTAW54ZnDo0MLglNSMmpCeVIGyRMxkCeiInsWIj+Dc9BKwVPOCgKicTaNo5vaq24GUgk1"
    "GSHFVO/6krYCN1TQtKn+LsOP5OQOFUDsaUQBw6+cqbcuo2Ylt8N8mqXCBOk0QJDsnCCBdJo2DKxsDZXUdhMfzerr"
    "sw0P3F3ay/EZsWN91sxRF7IHGeet7vrYwIvwputC5j7dqcLgIN21yaM/0aczXt10GWwo23dJ+1GPaNpW9s9yulzN"
    "kfGC7W4ROZW06ZXiqDQjar4FrupH9pGhXxB/WRQU9ieQWQ0hszLDwt31BaocI9f2GD/b4eEjZgOS9orEl+2gvAGY"
    "Da3QLvNmQ2apl3aw8qQVYyt2nAYEfuy60S3wY+f0mA0d2m1Q/3uMi5v3CPN93ew0hgiBi91FCFS1PFImfJHxkbX0"
    "y9gfLN1Qtw1ipJ32yZcZ5Bfl7I8f2ct0srnYcbH/HjUF22Qftgk7JqWdxOxYgiMu2suSOZ3DUqydpUR2etDixnO3"
    "vjhlsFvaabesNiLZlZyVBI1aQqPO7Mp1adPNxLusBsjOp0aqgUOyECB34uj88u7cdiUVQXMlshVFMDE13hB60cic"
    "cn2goZul6rEjw91p+VhzRFtPRmPjhb7WLN17QZy5WcBL50XVVI/rT4f0HXruxMIJv6+8isyK7U4ZaJKS7FgLumFN"
    "NQt7HqWBDCfgVUoT61TiHg4SUVe3X4jqKoFgSuJAUyEhgKkVphrUA4bMvQZYZU3n5bMepCKTLOdrKmOU5YPeIJ+t"
    "lbZXNbPrsCwuZMsfVJaWaTs+ZDb4AcdqEhuiKwk17c/6q0svXIeqTJ606ZQXPEiLaWVBVnDVMLI1WADNKhLXIIU/"
    "ue1i5wx43dpgyuUHFmz0VgxszkYHbypEf6qJLnAhNXAh3KUAPPx1efhzCTt1ZSGmUsbUQXerGXerJEQOpZbJUBSz"
    "aOHjssqI3FY8Q/gN0dD20o8dxDU0hVuLRki2XHFWSlF+ZBtVoyJgKtaO4gpDfl4W22QxkQM1kVJzqtZfpTyuBUW+"
    "EumcOoziWBJWTjFtvTYub+LYgScfi8OKHSp8cU0GeY4lIwgUS8O4sz1zLHsLEAKKRXF0gWJpCcXSnKo7LHxNzqEY"
    "OT5+xoYwUCdzvVdELNiplhCT017eID3O0jYZVxhMM6jeXRsPYyHP03mbT8ERXCsRNYHcStVuE9svWuCaMkimZYC+"
    "SlX6pYYfZ19aU+c3kdphlV/ZnXovZX7D07XkGYSUGARRQRAVEEFwlJUKyjgwFMomxKSt53sXPSMX2fyz7QUte2Ut"
    "bm2xFNqj8d2Mh/8w7PBF4M01ZFMQZFVLVhROkchsYXOkm/5cC5F3kUVvx62I9LquAHmBFynJtK8Ge2E/gDmT24Om"
    "2Aj3EKIFkt9ddVEp6gcwz2Cuh2dXalHaQEW8hX0A1hmsX7HrB7QMCqo6swU9AM7ZwA5Lx2ZFhHOywHhlwaWVpMx3"
    "srAuHLfqNBb2ARM5S9daFCDd9jVqYBlV1+eibgBxNr3Ycvzq6h5XHpaQLMj/CnAYv0lrIyTMaBbjsZBz5cmKmNdt"
    "sq7dD79dfPhA/u9uBW1Kf2YIVS6ZuvL1fPobj0Cl3CkHeVpzoRruacm9oH58pCDqkM3bCg9DPpsXPEdtGNfIc5Tz"
    "bcjw9Ov8IHc2Gjvkny17QbZNN2/HB7KRX4M8Z/rgJ9VvuxxfRupqr8h/EbKiKGwIAYPtdVREI8x1C4kjiTJC9URl"
    "bR3tLRcBfnZci7fpiUFcSagZ11Z/iCUUlGNQhIJy0viEC13UKofQ3x/vRnyEslIsRtjwO//umNhraLRLAUL0ljMa"
    "ZvL8/XLb/4N9NK+Gd5es6kg7uFSyaF/36u72fjgYD643sIy3veQ9Y5NWTCW9y+wcaSElI3m3EhMdwuLh/0Xa5N3n"
    "HileoDhyhCHXsSDXceq82aajT6WLTuYFD7LopEc35dCzJkmnZwWBR2ecFbrnvTnEgl64jo8MX95bwe0AYGa00J8L"
    "TBSEKoUCMpJq0nyK0HoQ6n9ohC14WFo3sHCmCaRwQArHelfH0OGeMp5t0Cvp8NBMZxsni4PTA5wee6Zd6nZ7oFfE"
    "s/4LUEwEAMEYQdd1XE1YGGGMfgqe+pygIkxgkSo2+GNczFYvNbHh3ehL0pylsOEc9hYqwjWEpNSnd/wjjNZ+QKIg"
    "i8z1Qq0jE/cNh1gfpDoCh1jLeHjDW67iBs8Jth0pRfy0/e/9m2H/cjhosJ/WcwLXQJoXWJbuvuchFYcW5CUhvGBN"
    "eEEElWaQbVoqiiMnuHuku//5HNhhnm1nEmDTx7b3K/2+/9pgbu8afwuR32PEMxbLBdLwZGEUqoyC79KtqsKCkxNs"
    "Bv70a1XCf1WloMIYcIVhHKqMQ5wR66OfHPtdzI4wYqqwTbsmRxau84qnPCeHWElMy6iC67b1w9Cylz6vJyulJpb1"
    "M6LYXgTkyXVeEO+0MjHtwIipFb5XW2CZE/iV4MvJHSh+hm7MUVjcVR5Druyh4gi0e3todwhAgQAUCEDhOIK+R9Wn"
    "7hHXDZS62ityAqVqWEHYSXv9PLREWYgT10QY2IGVe5yzhldKfs/GQvf67stFh/zzZF/1xxcd8s+T/dC/vLwhb6K/"
    "9Mr9Py/7D316OXr1ZH/t3z6OBw8XnfhFt4LJUb/5RpGVNd7SMmC6xcdSoFfESWgRLiHL9rtTCo6aoyKjnwvk4qSU"
    "dEnIskIHmTtlo5++Fk4drRKEQvkdzsIPHxoE6Mx13vw5jSMQnc2zfnNi+9ihA5kYNF8G2lGe1E6uXHTiF0929OI4"
    "+eQ4+eQk+eSkGTtSXJuazE6DG2EpnNx5wYNcI+ZE28Y28rwqEPJkDxJFU/d8rXomEUcc6JxmpRMBTdeKcW0qTdce"
    "w14i8jhVSt7w8Sv235cJRcxQxOKff39A5vIUVz6Ft+KS+nGncUZT854qEaf3V56JgyqB+6oSyJ9PhSQmM/FK8Zla"
    "7hEAclPZNbBXQG4ux3kThjPXyb5pznH/8XdtWUjqopN9/2QT8204HIyI3ZhqxPmQmpkPg/7v2uXd6NsjtTVX757s"
    "+8FYuyIfhNKpN0/2qH9LevnaJ52RS+l3VczUkzJm6onYTD3JmalpuLhjzn+6GDE16dOtHEe7IqTo8u/rlZjBlehB"
    "Wq1xyL14ISqM1N9o6dl3YbX6n/AYFdn9MyOmVgjMjiupgQXeUgucar+yj81KBsJkih6aZrAbbUIXgpBqMM+Zx78G"
    "0LIhROpCt1rYmhS+da1j8/1r6DF7NMjQdLklhJg2veIqQqS1FjvhPNp+q0n94TdAPn+zqJDUoHA1OoHGnJFqf246"
    "WnjRAyJh4jJSB2ndkt/oGthD0uDlBQ8Svzdya640eIzUQSLnmQgt5J/ZrNRBIveKfd2URo6ROkjkJo4dyO8TjNRB"
    "Iuc7VeYcI3WQyM1cfSrFHC8FlOSMj0pQxkdCxviIJYyj+hPk5niR4GIMGTElkaw/DDQu5mE6PFfGNTKwpZtFeC4l"
    "WXsiEv017qKR2BYZFIOrm9v+8Jfz3glzVkGC8mkOSuDZW8qzQ6X7VgwsVLoHjr8BRHVDE40f0DN5sOZjWlbiEXle"
    "dPc5sprXrFfEV7uRQFSvQvMike3H6f1I45zaX0mzzCUXvZIftrqUOj7oTyC490Vw/4+PZVT7uLmKBwWfn5bQ6M9P"
    "hRo9vQRHZ7Xz6KzU2iQ5klnJGkayUcaZggO5MHWDjMfkXZNc2jiiSjIX9a9zLiLbONGfokMUKz0knA7gWdn7s2Ih"
    "a4LowSMcJavoZE1GEo7UBHqqhSwGh54CGgNoDKAxImAfkRG42H/vB1MsOrMv16ZXRGB4cWtNp813k2UoZC+Aktjb"
    "kX70XDnplJ+s1LbS0LbKUNRfxMtF5EY8X1vo5AskwGTllDSEtpLUN/f9BVF7CRxSJ04yYkrieVRmeh6Jp+dRvjz4"
    "gipfRD+TOtkoK6UklKdlZuapeGKe5uZluIuRjVruCM+slJJQbuUpjw7PIkDxgocKQpozUmqlStYWcmXpHiVEhUet"
    "FJyhkJNUckaefSi3jxdt5IqHvNStJgGlUCul0OZ87MYwCnsjpysTCo+DcWf0bTjcLaPw1/8DzWbEWA=="
)
