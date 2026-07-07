from pathlib import Path

from django.test import Client

from shared_models.models import BookLoan


views_path = Path("librarian/views.py")
views_src = views_path.read_text(encoding="utf-8")


def assert_true(label, condition):
    print(f"{label}: {condition}")
    if not condition:
        raise AssertionError(label)


assert_true(
    "BookLoan create fields excludes late_risk",
    "class loans_book_loans_CreateView" in views_src
    and "model = BookLoan" in views_src
    and "fields = []" in views_src,
)
assert_true(
    "BookLoan update fields excludes late_risk",
    "class loans_book_loans_UpdateView" in views_src
    and "model = BookLoan" in views_src
    and "fields = []" in views_src,
)

client = Client()
assert_true(
    "demo_librarian login",
    client.login(username="demo_librarian", password="ai4mde-demo"),
)
response = client.get("/librarian/render_librarian_loans?create_book_loans=true")
assert_true("loans create page status 200", response.status_code == 200)
html = response.content.decode("utf-8")
assert_true("create form present", "loans_book_loans_create" in html)
assert_true("late_risk input absent", 'name="late_risk"' not in html)
assert_true("late_risk table header present", "<th>late_risk</th>" in html)
for expected in ["LOW", "MEDIUM", "HIGH"]:
    assert_true(f"seeded {expected} visible", expected in html)

print(f"BookLoan rows visible for HTML check: {BookLoan.objects.count()}")
print("PASS T2 form source/html checks")
