"""
Step 1 (Phase 1G) — Create test data in the GENERATED app and walk the relation chain.

CONTEXT: run this INSIDE the generated prototype's Django shell (studio-prototypes
container), NOT studio-api:
    docker compose exec studio-prototypes bash
    cd /usr/src/prototypes/generated_prototypes/<SYSTEM_ID>/LibraryStep1
    python manage.py migrate        # if generator.sh didn't already migrate
    python manage.py shell
    >>> exec(open('/path/to/step1_verify_shell.py').read())

CRITICAL — FK FIELD NAMES ARE PascalCase (named after the TARGET class), e.g.
    BookLoan.Loan, BookLoan.Book, Book.Author, Loan.Customer
Use PascalCase kwargs when creating objects. Reverse accessors are Django defaults
(lowercased model + _set): customer.loan_set, loan.bookloan_set, book.bookloan_set.

NOTE: BookLoan has no scalar attributes in Step 1, so its generated __str__ returns
str(self.Loan) (the generator uses the first FK when no scalar 'name'/str attr exists).
This is a benign generator quirk worth recording in the evidence file.
"""
from shared_models.models import Author, Book, Customer, Loan, BookLoan

# --- create (PascalCase FK kwargs) ------------------------------------------
a = Author.objects.create(name="Jane Austen", nationality="British")
b1 = Book.objects.create(title="Pride and Prejudice", isbn="001", year=1813,
                         category="FICTION", Author=a)
b2 = Book.objects.create(title="Emma", isbn="002", year=1815,
                         category="FICTION", Author=a)

c = Customer.objects.create(name="Alice", email="alice@example.com")
loan = Loan.objects.create(loan_date="2026-06-01", due_date="2026-06-15",
                           return_date="", Customer=c)

# BookLoan = associative class with TWO FKs (the Phase 1F payload)
bl1 = BookLoan.objects.create(Loan=loan, Book=b1)
bl2 = BookLoan.objects.create(Loan=loan, Book=b2)

# --- forward traversal (PascalCase) -----------------------------------------
print("bl1.Loan       =", bl1.Loan)
print("bl1.Book       =", bl1.Book)
print("bl1.Loan.Customer =", bl1.Loan.Customer)
print("bl1.Book.Author   =", bl1.Book.Author)

# --- reverse traversal (Django default _set) --------------------------------
print("c.loan_set       =", list(c.loan_set.all()))
print("loan.bookloan_set=", list(loan.bookloan_set.all()))
print("b1.bookloan_set  =", list(b1.bookloan_set.all()))
print("a.book_set       =", list(a.book_set.all()))

# --- full chain: Customer -> Loan -> BookLoan -> Book -> Author -------------
for ln in c.loan_set.all():
    for bl in ln.bookloan_set.all():
        print(f"Customer {c.name} | Loan {ln.id} | BookLoan {bl.id} "
              f"| Book {bl.Book.title} | Author {bl.Book.Author.name} "
              f"| category {bl.Book.category}")

# --- the Phase 1F assertions, re-checked at the ORM level -------------------
fk_fields = {f.name: f.related_model.__name__
             for f in BookLoan._meta.get_fields() if f.is_relation and f.many_to_one}
print("BookLoan FK fields:", fk_fields)
assert fk_fields.get("Loan") == "Loan", "BookLoan.Loan FK missing/incorrect"
assert fk_fields.get("Book") == "Book", "BookLoan.Book FK missing/incorrect"

# --- enum field sanity (Book.category) --------------------------------------
choice_values = [c[0] for c in Book.Category.choices]
print("Book.Category choices:", choice_values)
print("b1.category =", b1.category)
assert b1.category == "FICTION", "category value not persisted as expected"
for expected in ("FICTION", "NON_FICTION", "SCIENCE", "HISTORY", "CHILDREN"):
    assert expected in choice_values, f"missing enum choice {expected}"

print("PHASE 1F/1G GATE PASSED: BookLoan has two FKs -> Loan and Book; category enum intact")
