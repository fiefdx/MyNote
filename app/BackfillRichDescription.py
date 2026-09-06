# -*- coding: utf-8 -*-
'''
Created on 2026-09-05
@summary: One-off maintenance tool: recompute RICH notes' file_content and
          description from their rich_content, then re-index them.

Background
----------
`htmlparser.get_html_content()` used `page.itertext(allow_tags)`, which is an
element *selector*: it only yields the .text/.tail of elements whose tag is in
the list. `<body>` was not in the list, so the bare text nodes the rich editor
produces for plainly typed lines were dropped. The result: every rich note was
saved with `file_content = ""`, therefore `description = ""` (the note-list
preview stayed empty) and the whoosh index had no body text at all (body words
were not searchable).

That extraction bug is fixed in utils/htmlparser.py. This tool repairs the data
that was written while it was broken: for each rich note it re-derives
file_content + description from the stored rich_content and refreshes the
search index. It never changes rich_content, file_title, sha1 or created_at.

Usage (from the app directory, with the server stopped):

    python BackfillRichDescription.py --dry-run          # just report
    python BackfillRichDescription.py                    # apply (prompts for password)
    python BackfillRichDescription.py --user bob         # only one user
    python BackfillRichDescription.py --skip-index       # DB only
'''

import os
import sys
import time
import shutil
import logging
import argparse
import getpass

from config import CONFIG

import logger
sys.path.append(CONFIG["APP_PATH"])

from utils import htmlparser, common_utils
from models.item import RICH
import db.sqlite as db_sqlite
from db.sqlite import get_db_path
import db.db_rich as db_rich_mod
import ix.ix_rich as ix_rich_mod

LOG = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Rebuild rich notes' file_content / description from rich_content")
    parser.add_argument("--user", default=None, help="only process this user (default: all users)")
    parser.add_argument("--dry-run", action="store_true", help="report what would change, write nothing")
    parser.add_argument("--skip-index", action="store_true", help="do not refresh the whoosh index")
    parser.add_argument("--no-backup", action="store_true", help="do not copy RICH.db before writing")
    parser.add_argument("--password", default=None, help="login password (omit to be prompted; needed when ENCRYPT is on)")
    return parser.parse_args()


def get_key(args):
    """user_key is md5twice(password), same derivation as the login handler."""
    if not CONFIG["ENCRYPT"]:
        LOG.info("ENCRYPT is off, notes are stored in clear text.")
        return ""
    password = args.password
    if password is None:
        if not sys.stdin.isatty():
            LOG.error("ENCRYPT is on but no --password given and stdin is not a terminal.")
            return None
        password = getpass.getpass("Login password: ")
    return common_utils.md5twice(password)


def decrypt_note(note, key):
    """Decrypt in place. Returns False when the key is wrong (all fields become empty)."""
    stored_rich = note.rich_content
    note.decrypt(key)
    if stored_rich and not note.rich_content:
        return False
    return True


def main():
    args = parse_args()
    logger.config_logging(file_name = "rich_backfill.log",
                          log_level = CONFIG['LOG_LEVEL'],
                          dir_name = "logs",
                          day_rotate = False,
                          when = "D",
                          interval = 1,
                          max_size = 20,
                          backup_count = 5,
                          console = True)

    key = get_key(args)
    if key is None:
        return 2

    db_rich = db_rich_mod.DB()
    length = CONFIG["NOTE_DESCRIPTION_LENGTH"]

    # Collect the ids first: never write while a cursor on the same connection is iterating.
    if args.user:
        ids = [(n.id, n.user_name) for n in db_rich.get_rich_from_db_by_user_iter(args.user)]
    else:
        ids = [(n.id, n.user_name) for n in db_rich.get_rich_from_db_iter()]
    LOG.info("Found %s rich notes to check.", len(ids))
    if not ids:
        return 0

    # Validate the key on the first note before touching anything.
    probe = db_rich.get_rich_by_id(ids[0][0], ids[0][1])
    if key != "" and probe and not decrypt_note(probe, key):
        LOG.error("Wrong password: cannot decrypt rich note[%s]. Nothing was changed.", ids[0][0])
        return 2

    if not args.dry_run and not args.no_backup:
        db_path = get_db_path(CONFIG["STORAGE_DB_PATH"], "RICH")
        backup = "%s.bak-%s" % (db_path, time.strftime("%Y%m%d_%H%M%S"))
        shutil.copy2(db_path, backup)
        LOG.info("Backup of RICH.db written to %s", backup)

    ix_rich = None
    if not args.skip_index:
        ix_rich = ix_rich_mod.IX()

    changed = 0
    unchanged = 0
    failed = 0
    for note_id, user_name in ids:
        note = db_rich.get_rich_by_id(note_id, user_name)
        if not note:
            LOG.warning("Rich note[%s] disappeared, skipped.", note_id)
            continue
        if key != "" and not decrypt_note(note, key):
            LOG.error("Cannot decrypt rich note[%s], aborted.", note_id)
            return 2

        rich_content = note.rich_content or ""
        file_content = htmlparser.get_html_content(rich_content)["content"] if rich_content.strip() != "" else ""
        description = common_utils.get_description_text(file_content, length)

        if note.file_content == file_content and note.description == description:
            unchanged += 1
            LOG.debug("Rich note[%s] already up to date.", note_id)
            continue

        LOG.info("Rich note[%s] user[%s] title[%s]", note_id, user_name, note.file_title)
        LOG.info("    file_content: %r -> %r", note.file_content, file_content)
        LOG.info("    description : %r -> %r", note.description, description)
        if args.dry_run:
            changed += 1
            continue

        note.file_content = file_content
        note.description = description
        if key != "":
            if not note.encrypt(key):
                LOG.error("Cannot encrypt rich note[%s], aborted.", note_id)
                return 2
        if db_rich.save_data_to_db(note.to_dict(), mode = "UPDATE") != True:
            failed += 1
            LOG.error("Failed to write rich note[%s].", note_id)
            continue
        changed += 1

        if ix_rich is not None:
            # index_rich_by_id re-reads the row and decrypts it with key itself.
            if ix_rich.index_rich_by_id(note_id, user_name, key = key, db_rich = db_rich) != True:
                LOG.warning("Failed to re-index rich note[%s].", note_id)
        # keep the console readable on large libraries
        time.sleep(0)

    LOG.info("Done. changed=%s unchanged=%s failed=%s dry_run=%s", changed, unchanged, failed, args.dry_run)

    if ix_rich is not None:
        ix_rich.close()
    db_rich.close()
    db_sqlite.DB.cls_close()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
