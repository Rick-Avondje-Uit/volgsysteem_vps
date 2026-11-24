from __future__ import annotations

import re

from django.db import migrations


TABLE_NAME = "core_deelnemer"
NEW_TABLE_NAME = "core_deelnemer_pk_new"
BACKUP_TABLE_NAME = "core_deelnemer_pk_backup"


def restore_deelnemer_primary_key(apps, schema_editor):
    connection = schema_editor.connection

    if connection.vendor != "sqlite":
        raise RuntimeError(
            "Deze herstelmigratie is uitsluitend bedoeld voor SQLite."
        )

    quote = connection.ops.quote_name

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type = 'table' AND name = %s",
            [TABLE_NAME],
        )
        row = cursor.fetchone()

        if not row or not row[0]:
            raise RuntimeError(
                f"Tabel {TABLE_NAME!r} is niet gevonden."
            )

        original_create_sql = row[0]

        cursor.execute(
            f"PRAGMA table_info({quote(TABLE_NAME)})"
        )
        table_info = cursor.fetchall()

        id_columns = [column for column in table_info if column[1] == "id"]
        if len(id_columns) != 1:
            raise RuntimeError(
                f"Verwacht exact een id-kolom in {TABLE_NAME!r}."
            )

        # PRAGMA table_info: cid, name, type, notnull, default, pk
        if id_columns[0][5] == 1:
            # De database is al correct; de migratie is idempotent.
            return

        cursor.execute(
            f"SELECT id, COUNT(*) "
            f"FROM {quote(TABLE_NAME)} "
            "GROUP BY id "
            "HAVING id IS NULL OR COUNT(*) > 1 "
            "LIMIT 1"
        )
        invalid_id = cursor.fetchone()
        if invalid_id:
            raise RuntimeError(
                "De primary key kan niet veilig worden hersteld: "
                f"ongeldige of dubbele deelnemer-id gevonden: {invalid_id!r}."
            )

        cursor.execute(
            f"SELECT COUNT(*) FROM {quote(TABLE_NAME)}"
        )
        original_count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT name, sql FROM sqlite_master "
            "WHERE type = 'index' AND tbl_name = %s AND sql IS NOT NULL",
            [TABLE_NAME],
        )
        indexes = cursor.fetchall()

        # Wijzig uitsluitend de tabelnaam en de definitie van de bestaande
        # id-kolom. Alle overige kolommen en constraints blijven behouden.
        create_sql = re.sub(
            rf"(?i)^CREATE\s+TABLE\s+(?:['\"]?{re.escape(TABLE_NAME)}['\"]?)",
            f"CREATE TABLE {quote(NEW_TABLE_NAME)}",
            original_create_sql,
            count=1,
        )
        create_sql, replacements = re.subn(
            r"(?i)([('\"`\s,])id\s+integer(\s*(?:,|\)))",
            r"\1id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT\2",
            create_sql,
            count=1,
        )

        if replacements != 1:
            raise RuntimeError(
                "De id-kolom kon niet veilig in de bestaande CREATE TABLE-SQL "
                "worden herkend. De database is niet gewijzigd."
            )

        columns = [column[1] for column in table_info]
        quoted_columns = ", ".join(quote(column) for column in columns)

        cursor.execute("PRAGMA foreign_keys = OFF")

        try:
            cursor.execute("BEGIN IMMEDIATE")

            cursor.execute(
                f"DROP TABLE IF EXISTS {quote(NEW_TABLE_NAME)}"
            )
            cursor.execute(
                f"DROP TABLE IF EXISTS {quote(BACKUP_TABLE_NAME)}"
            )

            # Data-back-up binnen hetzelfde databasebestand. Deze tabel is
            # bewust constraintloos en wordt na een geslaagde migratie bewaard.
            cursor.execute(
                f"CREATE TABLE {quote(BACKUP_TABLE_NAME)} AS "
                f"SELECT * FROM {quote(TABLE_NAME)}"
            )

            cursor.execute(create_sql)
            cursor.execute(
                f"INSERT INTO {quote(NEW_TABLE_NAME)} ({quoted_columns}) "
                f"SELECT {quoted_columns} FROM {quote(TABLE_NAME)}"
            )

            cursor.execute(
                f"SELECT COUNT(*) FROM {quote(NEW_TABLE_NAME)}"
            )
            copied_count = cursor.fetchone()[0]
            if copied_count != original_count:
                raise RuntimeError(
                    "Niet alle deelnemers zijn naar de herstelde tabel gekopieerd: "
                    f"verwacht {original_count}, gekopieerd {copied_count}."
                )

            cursor.execute(f"DROP TABLE {quote(TABLE_NAME)}")
            cursor.execute(
                f"ALTER TABLE {quote(NEW_TABLE_NAME)} "
                f"RENAME TO {quote(TABLE_NAME)}"
            )

            for _, index_sql in indexes:
                cursor.execute(index_sql)

            cursor.execute("PRAGMA foreign_key_check")
            violations = cursor.fetchall()
            if violations:
                raise RuntimeError(
                    "Foreign-keycontrole na herstel is mislukt: "
                    f"{violations[:10]!r}"
                )

            cursor.execute(
                f"PRAGMA table_info({quote(TABLE_NAME)})"
            )
            repaired_info = cursor.fetchall()
            repaired_id = [
                column for column in repaired_info if column[1] == "id"
            ]
            if len(repaired_id) != 1 or repaired_id[0][5] != 1:
                raise RuntimeError(
                    "De id-kolom is na het herbouwen nog geen primary key."
                )

            cursor.execute("COMMIT")
        except Exception:
            cursor.execute("ROLLBACK")
            raise
        finally:
            cursor.execute("PRAGMA foreign_keys = ON")


def reverse_restore_deelnemer_primary_key(apps, schema_editor):
    raise RuntimeError(
        "Deze databasereparatie kan niet veilig automatisch worden teruggedraaid. "
        "Herstel zo nodig de databaseback-up die voor de migratie is gemaakt."
    )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        # Vervang dit door de naam van je laatste core-migratie.
        ("core", "0002_weeztixoauthtoken"),
    ]

    operations = [
        migrations.RunPython(
            restore_deelnemer_primary_key,
            reverse_restore_deelnemer_primary_key,
        ),
    ]
