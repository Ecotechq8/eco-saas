# -*- coding: utf-8 -*-


def _column_exists(cr, table_name, column_name):
    cr.execute("""
        SELECT 1
          FROM information_schema.columns
         WHERE table_schema = 'public'
           AND table_name = %s
           AND column_name = %s
         LIMIT 1
    """, (table_name, column_name))
    return bool(cr.fetchone())


def migrate(cr, version):
    if not _column_exists(cr, 'hr_attendance', 'state'):
        cr.execute("""
            ALTER TABLE hr_attendance
                ADD COLUMN state varchar
        """)

    cr.execute("""
        UPDATE hr_attendance
           SET state = 'draft'
         WHERE state IS NULL
    """)

    if not _column_exists(cr, 'hr_attendance', 'e_modified_time'):
        cr.execute("""
            ALTER TABLE hr_attendance
                ADD COLUMN e_modified_time timestamp
        """)
