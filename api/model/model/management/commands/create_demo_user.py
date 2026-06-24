from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a demo (non-admin) user for public testing. Idempotent."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="demo")
        parser.add_argument("--password", default="demo")
        parser.add_argument("--email", default="demo@localhost")

    def handle(self, *args, **options):
        user_model = get_user_model()
        username = options["username"]
        password = options["password"]
        email = options["email"]

        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": False, "is_superuser": False},
        )
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Demo user '{username}' created."))
        else:
            self.stdout.write(f"Demo user '{username}' already exists — password updated.")
