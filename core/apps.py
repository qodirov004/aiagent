"""core app configuration."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "O'quv Markazi"

    def ready(self):
        # Python 3.14 compatibility for Django BaseContext.__copy__
        try:
            from django.template.context import BaseContext

            def _base_context_copy(self):
                cls = self.__class__
                dup = cls.__new__(cls)
                dup.__dict__.update(self.__dict__)
                dup.dicts = self.dicts[:]
                return dup

            BaseContext.__copy__ = _base_context_copy
        except Exception:
            pass

