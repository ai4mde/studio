from django.apps import AppConfig


class SharedModelsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shared_models"

    def ready(self):
        import shared_models.ai_hooks  # noqa: F401  (registers M07 post_save receivers)
        from shared_models import ai_actions
        ai_actions.attach_actions()