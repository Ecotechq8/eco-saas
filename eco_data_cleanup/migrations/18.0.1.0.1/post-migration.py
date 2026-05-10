# -*- coding: utf-8 -*-

import logging
import re

_logger = logging.getLogger(__name__)


def _table_exists(cr, table_name):
    cr.execute("""
        SELECT 1
          FROM information_schema.tables
         WHERE table_schema = 'public'
           AND table_name = %s
         LIMIT 1
    """, (table_name,))
    return bool(cr.fetchone())


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


def _execute_safe(cr, query, params=None, label='cleanup repair'):
    savepoint = 'sp_%s' % re.sub(r'[^A-Za-z0-9_]', '_', label)[:40]
    try:
        cr.execute('SAVEPOINT %s' % savepoint)
        cr.execute(query, params or ())
        count = cr.rowcount
        cr.execute('RELEASE SAVEPOINT %s' % savepoint)
        if count:
            _logger.info('%s: repaired %s row(s)', label, count)
        return count
    except Exception as exc:
        try:
            cr.execute('ROLLBACK TO SAVEPOINT %s' % savepoint)
        except Exception:
            pass
        _logger.warning('%s skipped: %s', label, exc)
        return 0


def migrate(cr, version):
    """Repair stale project.task references left by older raw SQL cleanup."""
    if not _table_exists(cr, 'project_task'):
        return

    repaired = 0

    if _column_exists(cr, 'account_move_line', 'task_id'):
        repaired += _execute_safe(cr, """
            UPDATE account_move_line aml
               SET task_id = NULL
             WHERE task_id IS NOT NULL
               AND NOT EXISTS (
                   SELECT 1 FROM project_task pt WHERE pt.id = aml.task_id
               )
        """, label='account_move_line.task_id')

    if _column_exists(cr, 'helpdesk_ticket', 'task_id'):
        repaired += _execute_safe(cr, """
            UPDATE helpdesk_ticket ht
               SET task_id = NULL
             WHERE task_id IS NOT NULL
               AND NOT EXISTS (
                   SELECT 1 FROM project_task pt WHERE pt.id = ht.task_id
               )
        """, label='helpdesk_ticket.task_id')

    reference_tables = (
        ('mail_activity', 'res_model'),
        ('mail_followers', 'res_model'),
        ('mail_message', 'model'),
        ('ir_attachment', 'res_model'),
        ('ir_model_data', 'model'),
    )
    for table_name, model_field in reference_tables:
        if _table_exists(cr, table_name) and _column_exists(cr, table_name, 'res_id'):
            repaired += _execute_safe(cr, f"""
                DELETE FROM {table_name} ref
                 WHERE {model_field} = %s
                   AND NOT EXISTS (
                       SELECT 1 FROM project_task pt WHERE pt.id = ref.res_id
                   )
            """, ('project.task',), table_name)

    for table_name in ('helpdesk_ticket_project_task_rel', 'ticket_helpdesk_project_task_rel'):
        if _column_exists(cr, table_name, 'project_task_id'):
            repaired += _execute_safe(cr, f"""
                DELETE FROM {table_name} rel
                 WHERE NOT EXISTS (
                     SELECT 1 FROM project_task pt WHERE pt.id = rel.project_task_id
                 )
            """, label=table_name)

    _logger.info('eco_data_cleanup stale project.task repair completed: %s row(s)', repaired)
