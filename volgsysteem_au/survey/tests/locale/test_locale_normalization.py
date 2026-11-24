import logging
import subprocess
import sys
import unittest
from pathlib import Path
from django.conf import settings
from django.test import TestCase

class TestLocaleNormalization(unittest.TestCase):

    LOCALE_PATH = Path("survey", "locale").absolute()

    def test_normalization(self):
        """
        Controleert of de vertaalbestanden overeenkomen met de output
        van makemessages --no-obsolete --no-wrap.
        """

        makemessages_command = [
            sys.executable,
            "manage.py",
            "makemessages",
            "--no-obsolete",
            "--no-wrap",
            "--ignore",
            ".venv",
        ]

        for language_code , _language_name in settings.LANGUAGES:
            if language_code != "en":
                makemessages_command += ["--locale", language_code]

        logging.warning(
            "Command to launch for makemessages is: %s",
            " ".join(makemessages_command),
        )

        subprocess.check_call(makemessages_command)

        git_check = subprocess.run(
		    ["git", "rev-parse", "--is-inside-work-tree"],
		    capture_output=True,
		    text=True,
		    check=False,
	    )

        if git_check.returncode != 0:
            self.skipTest(
                "Git repository niet beschikbaar; "
                "controle van wijzigingen in survey/locale wordt overgeslagen."
            )

        git_diff_command = [
            "git",
            "diff",
            "--exit-code",
            "--",
            str(self.LOCALE_PATH),
        ]

        result = subprocess.run(
            git_diff_command,
            capture_output=True,
            text=True,
            check=False,
        )

        msg = (
            "De vertaalbestanden zijn niet bijgewerkt. "
            "Voer makemessages uit en voeg de wijzigingen in survey/locale toe aan Git.\n\n"
            f"{result.stdout}"
            f"{result.stderr}"
        )

        self.assertEqual(
            result.returncode,
            0,
            msg,
        )
