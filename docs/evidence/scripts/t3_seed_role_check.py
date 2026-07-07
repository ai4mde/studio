from django.contrib.auth.hashers import check_password

from shared_models.models import Author, Book, BookLoan, Customer, Loan, User


EXPECTED_PASSWORD = "ai4mde-demo"


def assert_equal(label, actual, expected):
    print(f"{label}: {actual}")
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected}, got {actual}")


def assert_true(label, condition):
    print(f"{label}: {condition}")
    if not condition:
        raise AssertionError(label)


assert_equal("User count", User.objects.count(), 2)
assert_equal("Author count", Author.objects.count(), 3)
assert_equal("Book count", Book.objects.count(), 6)
assert_equal("Customer count", Customer.objects.count(), 2)
assert_equal("Loan count", Loan.objects.count(), 5)
assert_equal("BookLoan count", BookLoan.objects.count(), 5)

user_fields = {field.name for field in User._meta.fields}
print(f"User fields: {sorted(user_fields)}")
assert_true("User has is_librarian", "is_librarian" in user_fields)
assert_true("User has is_member", "is_member" in user_fields)

demo_librarian = User.objects.get(username="demo_librarian")
demo_member = User.objects.get(username="demo_member")
assert_true(
    "demo_librarian password valid",
    check_password(EXPECTED_PASSWORD, demo_librarian.password),
)
assert_true(
    "demo_member password valid",
    check_password(EXPECTED_PASSWORD, demo_member.password),
)
assert_true("demo_librarian is_librarian", demo_librarian.is_librarian)
assert_true("demo_member is_member", demo_member.is_member)

late_risks = list(BookLoan.objects.order_by("id").values_list("late_risk", flat=True))
print(f"BookLoan late_risk values: {late_risks}")
assert_true("Seeded BookLoan late_risk all populated", all(late_risks))
assert_true(
    "Seed left alice.reading_plan empty",
    Customer.objects.get(name="alice").reading_plan in ("", None),
)
print("PASS T3 seed and role check")
