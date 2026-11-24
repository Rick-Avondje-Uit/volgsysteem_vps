from django.contrib.staticfiles.finders import get_finders
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = ("Zoekt naar conflicterende Django static bestanden.")

    def handle(self, *args, **options):
        bestanden = {}

        for finder in get_finders():
            for path, storage in finder.list([]):
                bestanden.setdefault(path, set())

                try:
                    locatie = storage.path(path)
                except NotImplementedError:
                    locatie = f'Remote storage: {storage}'

                bestanden[path].add(locatie)

        conflicten = {
            path: locaties
            for path, locaties in bestanden.items()
            if len(locaties) > 1
        }

        if not conflicten:
            self.stdout.write(
                self.style.SUCCESS(
                "Geen conflicterende static bestanden gevonden."
                )
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f"{len(conflicten)} static-conflicten gevonden."
            )
        )

        for path, locaties in sorted(conflicten.items()):
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(path)
            )

            for locatie in locaties:
                self.stdout.write(
                    f"  -> {locatie}"
                )

