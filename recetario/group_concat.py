from django.db.models import Aggregate, CharField
from django.db.models.expressions import Combinable


class GroupConcat(Aggregate):
    output_field = CharField()

    def __init__(
        self,
        expression,
        separator=", ",
        distinct=False,
        ordering=None,
        **extra
    ):
        self.separator = separator
        self.distinct = distinct
        self.ordering = ordering
        super().__init__(expression, **extra)

    def as_sql(self, compiler, connection, **extra_context):
        expr_sql, params = compiler.compile(self.source_expressions[0])

        vendor = connection.vendor

        if vendor == "sqlite":
            # SQLite: GROUP_CONCAT(expr, separator)
            sql = f"GROUP_CONCAT({expr_sql}"
            if self.separator:
                sql += f", '{self.separator}'"
            sql += ")"
            return sql, params

        elif vendor == "mysql":
            # MySQL: GROUP_CONCAT(DISTINCT expr ORDER BY ... SEPARATOR ...)
            distinct_sql = "DISTINCT " if self.distinct else ""
            ordering_sql = f" ORDER BY {self.ordering}" if self.ordering else ""
            separator_sql = f' SEPARATOR "{self.separator}"' if self.separator else ""

            sql = f"GROUP_CONCAT({distinct_sql}{expr_sql}{ordering_sql}{separator_sql})"

            return sql, params

        else:
            # Para PostgreSQL u otros: usar STRING_AGG
            order_sql = f" ORDER BY {self.ordering}" if self.ordering else ""
            sql = f"STRING_AGG({expr_sql}, '{self.separator}'){order_sql}"
            return sql, params

    # Implementamos métodos abstractos para Combinable
    def __rand__(self, other: object) -> Combinable:
        return NotImplemented

    def __ror__(self, other: object) -> Combinable:
        return NotImplemented

    def __rxor__(self, other: object) -> Combinable:
        return NotImplemented
