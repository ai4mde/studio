from django.contrib.auth.hashers import make_password
from django.db import migrations


DEMO_PASSWORD = "ai4mde-demo"


def has_field(model, name):
    try:
        model._meta.get_field(name)
        return True
    except Exception:
        return False


def pick_field(model, *names):
    for name in names:
        if has_field(model, name):
            return name
    return None


def required_fields_available(field_map):
    return all(field_map.values())


def seed_library_demo_data(apps, schema_editor):
    try:
        User = apps.get_model("shared_models", "User")
        Author = apps.get_model("shared_models", "Author")
        Book = apps.get_model("shared_models", "Book")
        Customer = apps.get_model("shared_models", "Customer")
        Loan = apps.get_model("shared_models", "Loan")
        BookLoan = apps.get_model("shared_models", "BookLoan")
    except LookupError:
        return

    fields = {
        "author_name": pick_field(Author, "name"),
        "book_title": pick_field(Book, "title"),
        "book_category": pick_field(Book, "category"),
        "book_author": pick_field(Book, "author", "Author"),
        "customer_name": pick_field(Customer, "name"),
        "loan_customer": pick_field(Loan, "customer", "Customer"),
        "bookloan_loan": pick_field(BookLoan, "loan", "Loan"),
        "bookloan_book": pick_field(BookLoan, "book", "Book"),
        "bookloan_late_risk": pick_field(BookLoan, "late_risk"),
    }
    if not required_fields_available(fields):
        return

    user_rows = [
        {"username": "demo_librarian", "password": make_password(DEMO_PASSWORD)},
        {
            # Created for T3 readiness; role flag is set only if the generated
            # User model contains is_member.
            "username": "demo_member",
            "password": make_password(DEMO_PASSWORD),
        },
    ]
    if has_field(User, "is_librarian"):
        user_rows[0]["is_librarian"] = True
    if has_field(User, "is_member"):
        user_rows[1]["is_member"] = True
    User.objects.bulk_create([User(**row) for row in user_rows])

    authors_data = [
        ("Ursula K. Le Guin", "US"),
        ("Octavia E. Butler", "US"),
        ("Terry Pratchett", "UK"),
    ]
    Author.objects.bulk_create(
        [
            Author(
                **{
                    fields["author_name"]: name,
                    **({"nationality": nationality} if has_field(Author, "nationality") else {}),
                }
            )
            for name, nationality in authors_data
        ]
    )
    authors = {
        getattr(author, fields["author_name"]): author
        for author in Author.objects.filter(
            **{f"{fields['author_name']}__in": [row[0] for row in authors_data]}
        )
    }

    books_data = [
        ("A Wizard of Earthsea", "FICTION", "Ursula K. Le Guin", "9780547773742", 1968),
        ("The Left Hand of Darkness", "SCIENCE", "Ursula K. Le Guin", "9780441478125", 1969),
        ("Kindred", "HISTORY", "Octavia E. Butler", "9780807083697", 1979),
        ("Parable of the Sower", "SCIENCE", "Octavia E. Butler", "9780446675505", 1993),
        ("Guards! Guards!", "FICTION", "Terry Pratchett", "9780062225757", 1989),
        ("A Hat Full of Sky", "CHILDREN", "Terry Pratchett", "9780060586621", 2004),
    ]
    book_rows = []
    for title, category, author_name, isbn, year in books_data:
        kwargs = {
            fields["book_title"]: title,
            fields["book_category"]: category,
            fields["book_author"]: authors[author_name],
        }
        if has_field(Book, "isbn"):
            kwargs["isbn"] = isbn
        if has_field(Book, "year"):
            kwargs["year"] = year
        book_rows.append(Book(**kwargs))
    Book.objects.bulk_create(book_rows)
    books = {
        getattr(book, fields["book_title"]): book
        for book in Book.objects.filter(
            **{f"{fields['book_title']}__in": [row[0] for row in books_data]}
        )
    }

    customers_data = [
        ("alice", "alice@example.com"),
        ("bob", "bob@example.com"),
    ]
    Customer.objects.bulk_create(
        [
            Customer(
                **{
                    fields["customer_name"]: name,
                    **({"email": email} if has_field(Customer, "email") else {}),
                }
            )
            for name, email in customers_data
        ]
    )
    customers = {
        getattr(customer, fields["customer_name"]): customer
        for customer in Customer.objects.filter(
            **{f"{fields['customer_name']}__in": [row[0] for row in customers_data]}
        )
    }
    alice = customers["alice"]

    loan_history = [
        ("2026-01-01", "2026-01-15", "2026-01-14", "A Wizard of Earthsea", "LOW"),
        ("2026-02-01", "2026-02-15", "2026-02-14", "The Left Hand of Darkness", "LOW"),
        ("2026-03-01", "2026-03-15", "2026-03-16", "Parable of the Sower", "MEDIUM"),
        ("2026-04-01", "2026-04-15", "2026-04-14", "Kindred", "LOW"),
        ("2026-05-01", "2026-05-15", "2026-05-20", "Guards! Guards!", "HIGH"),
    ]
    loan_rows = []
    for loan_date, due_date, return_date, _book_title, _late_risk in loan_history:
        kwargs = {fields["loan_customer"]: alice}
        if has_field(Loan, "loan_date"):
            kwargs["loan_date"] = loan_date
        if has_field(Loan, "due_date"):
            kwargs["due_date"] = due_date
        if has_field(Loan, "return_date"):
            kwargs["return_date"] = return_date
        loan_rows.append(Loan(**kwargs))
    loans = Loan.objects.bulk_create(loan_rows)
    if any(loan.pk is None for loan in loans):
        loans = list(
            Loan.objects.filter(
                **{f"loan_date__in": [row[0] for row in loan_history]},
                **{fields["loan_customer"]: alice},
            ).order_by("loan_date")
        )

    bookloan_rows = []
    for loan, (_loan_date, _due_date, _return_date, book_title, late_risk) in zip(
        loans, loan_history
    ):
        bookloan_rows.append(
            BookLoan(
                **{
                    fields["bookloan_loan"]: loan,
                    fields["bookloan_book"]: books[book_title],
                    fields["bookloan_late_risk"]: late_risk,
                }
            )
        )
    BookLoan.objects.bulk_create(bookloan_rows)


class Migration(migrations.Migration):
    dependencies = [
        ("shared_models", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_library_demo_data, migrations.RunPython.noop),
    ]
