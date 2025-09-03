from django.db.models import Aggregate, CharField


class GroupConcat(Aggregate):
    function = "GROUP_CONCAT"
    template = "%(function)s(%(distinct)s%(expressions)s%(ordering)s%(separator)s)"
    allow_distinct = True

    def __init__(
        self, expression, distinct=False, separator=", ", ordering=None, **extra
    ):
        super().__init__(
            expression,
            distinct="DISTINCT " if distinct else "",
            separator=f' SEPARATOR "{separator}"' if separator else "",
            ordering=f" ORDER BY {ordering}" if ordering else "",
            output_field=CharField(),
            **extra,
        )

    # Implementamos métodos abstractos para Combinable
    def __rand__(self, other):
        return NotImplemented

    def __ror__(self, other):
        return NotImplemented

    def __rxor__(self, other):
        return NotImplemented
