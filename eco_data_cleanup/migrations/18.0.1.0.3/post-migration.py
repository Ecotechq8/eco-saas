# -*- coding: utf-8 -*-

import logging
import re

_logger = logging.getLogger(__name__)
IDENTIFIER_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def _safe_identifier(identifier):
    return bool(identifier and IDENTIFIER_RE.match(identifier))


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


def _repair_many2one_fields(cr, relation_model, target_table):
    if not (_table_exists(cr, target_table) and _table_exists(cr, 'ir_model') and _table_exists(cr, 'ir_model_fields')):
        return 0

    repaired = 0
    cr.execute("""
        SELECT m.model, f.name
          FROM ir_model_fields f
          JOIN ir_model m ON m.id = f.model_id
         WHERE f.ttype = 'many2one'
           AND f.relation = %s
           AND COALESCE(f.store, TRUE) = TRUE
    """, (relation_model,))
    for model_name, field_name in cr.fetchall():
        table_name = model_name.replace('.', '_')
        if not (
                _safe_identifier(table_name)
                and _safe_identifier(field_name)
                and _table_exists(cr, table_name)
                and _column_exists(cr, table_name, field_name)):
            continue

        repaired += _execute_safe(cr, f"""
            UPDATE {table_name} ref
               SET {field_name} = NULL
             WHERE {field_name} IS NOT NULL
               AND NOT EXISTS (
                   SELECT 1 FROM {target_table} target WHERE target.id = ref.{field_name}
               )
        """, label=f'{table_name}.{field_name}')
    return repaired


def _repair_relation_tables(cr, target_table):
    if not _table_exists(cr, target_table):
        return 0

    repaired = 0
    column_name = '%s_id' % target_table
    cr.execute("""
        SELECT table_name
          FROM information_schema.columns
         WHERE table_schema = 'public'
           AND column_name = %s
    """, (column_name,))
    for (table_name,) in cr.fetchall():
        if not (_safe_identifier(table_name) and _table_exists(cr, table_name)):
            continue

        repaired += _execute_safe(cr, f"""
            DELETE FROM {table_name} rel
             WHERE {column_name} IS NOT NULL
               AND NOT EXISTS (
                   SELECT 1 FROM {target_table} target WHERE target.id = rel.{column_name}
               )
        """, label=table_name)
    return repaired


def _repair_reference_tables(cr, relation_model, target_table):
    if not _table_exists(cr, target_table):
        return 0

    repaired = 0
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
                       SELECT 1 FROM {target_table} target WHERE target.id = ref.res_id
                   )
            """, (relation_model,), table_name)
    return repaired


def _repair_defaults(cr, relation_model, target_table):
    if not (_table_exists(cr, target_table) and _table_exists(cr, 'ir_default') and _table_exists(cr, 'ir_model_fields')):
        return 0

    repaired = 0
    for value_column in ('json_value', 'value'):
        if _column_exists(cr, 'ir_default', value_column):
            repaired += _execute_safe(cr, f"""
                DELETE FROM ir_default d
                 USING ir_model_fields f
                 WHERE d.field_id = f.id
                   AND f.ttype = 'many2one'
                   AND f.relation = %s
                   AND NULLIF(regexp_replace(d.{value_column}::text, '[^0-9]', '', 'g'), '')::integer NOT IN (
                       SELECT id FROM {target_table}
                   )
            """, (relation_model,), f'ir_default.{value_column}.{relation_model}')
    return repaired


def _repair_model(cr, relation_model, target_table):
    repaired = 0
    repaired += _repair_many2one_fields(cr, relation_model, target_table)
    repaired += _repair_relation_tables(cr, target_table)
    repaired += _repair_reference_tables(cr, relation_model, target_table)
    repaired += _repair_defaults(cr, relation_model, target_table)
    return repaired


def migrate(cr, version):
    repaired = 0
    repaired += _repair_model(cr, 'project.task', 'project_task')
    repaired += _repair_model(cr, 'project.project', 'project_project')
    _logger.info('eco_data_cleanup stale project repair completed: %s row(s)', repaired)
