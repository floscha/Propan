from functools import wraps
from inspect import signature
from typing import Callable, Any, Dict

from pydantic import BaseConfig
from pydantic.fields import ModelField, Undefined

from propan.utils.context.types import Alias, Depends


NOT_CAST = (Alias, Depends)


def apply_types(func: Callable) -> Callable:
    sig = signature(func).parameters
    arg_names = tuple(sig.keys())

    annotations = {}
    for name, param in sig.items():
        if type(param.default) not in NOT_CAST and any((
            (has_annotation := (param.annotation != param.empty)),
            (has_default := (param.default != param.empty))
        )):
            annotations[name] = ModelField(
                name=name,
                type_=param.annotation if has_annotation else type(param.default),
                default=param.default if has_default else Undefined,
                class_validators=None,
                required=not has_default,
                model_config=BaseConfig,
            )

    def _cast_type(arg_name: str, arg_value: Any, values: Dict[str, Any]):
        if (arg_type := annotations.get(arg_name)) is not None:
            arg_value, err = arg_type.validate(arg_value, values, loc=arg_type.alias)
            if err:
                raise ValueError(err)
        return arg_value

    @wraps(func)
    def wrapper(*args, **kwargs):
        kw = {
            k: v for k, v in (*zip(arg_names, args), *kwargs.items())
        }

        kw = {
            arg_name: _cast_type(arg_name, arg_value, kw)
            for arg_name, arg_value in kw.items()
        }

        return func(**kw)
    return wrapper
