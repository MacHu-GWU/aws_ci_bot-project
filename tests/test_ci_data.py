# -*- coding: utf-8 -*-

import os
from aws_ci_bot.ci_data import CIData, CI_DATA_PREFIX


class TestCIData:
    def test_dump_and_load(self):
        # dump
        ci_data = CIData(
            event_s3_console_url="https://www.aws.com",
            commit_message="chore",
            comment_id="85681fb8b8d654410b805dab8758969e",
        )
        assert ci_data.to_env_var() == {
            "CI_DATA_EVENT_S3_CONSOLE_URL": "https://www.aws.com",
            "CI_DATA_COMMIT_MESSAGE": "chore",
            "CI_DATA_COMMENT_ID": "85681fb8b8d654410b805dab8758969e",
        }

        # load
        os.environ[f"{CI_DATA_PREFIX}COMMENT_ID"] = "c85d8e148751900eb2c9d80846eeecac"
        ci_data = CIData.from_env_var(os.environ)
        assert ci_data.comment_id == "c85d8e148751900eb2c9d80846eeecac"


if __name__ == "__main__":
    from aws_ci_bot.tests import run_cov_test

    run_cov_test(__file__, "aws_ci_bot.ci_data", preview=False)
