from ast import Expression
from typing import Any, Optional, Union
from django.db.models import Aggregate, CharField, F
from django.db.models.expressions import Combinable


class GroupConcat(Aggregate):
    function = "GROUP_CONCAT"
    template = "%(function)s(%(distinct)s%(expressions)s%(ordering)s%(separator)s)"
    allow_distinct = True

    def __init__(
        self,
        expression: Union[Expression, F, str],
        distinct: bool = False,
        separator: Optional[str] = ", ",
        ordering: Optional[str] = None,
        **extra: Any,
    ) -> None:
        super().__init__(
            expression,
            distinct=distinct,
            separator=f' SEPARATOR "{separator}"' if separator else "",
            ordering=f" ORDER BY {ordering}" if ordering else "",
            output_field=CharField(),
            **extra,
        )

    # Implementamos métodos abstractos para Combinable
    def __rand__(self, other: object) -> Combinable:
        return NotImplemented

    def __ror__(self, other: object) -> Combinable:
        return NotImplemented

    def __rxor__(self, other: object) -> Combinable:
        return NotImplemented
