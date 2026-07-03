#!/usr/bin/env bash
set -e

SITE_DIR=site

rm -rf "$SITE_DIR"
mkdir -p "$SITE_DIR/backend" "$SITE_DIR/guides" "$SITE_DIR/frontend"

# -------------------------
# Backend (Sphinx)
# -------------------------

sphinx-apidoc -f \
  -o docs/backend/source/api \
  api/model \
  */migrations */__pycache__ \
  --templatedir=docs/backend/templates

sphinx-build -b html \
  docs/backend/source \
  "$SITE_DIR/backend" \
  -E -a -v

# -------------------------
# Guides (Sphinx)
# -------------------------

sphinx-build -b html \
  docs/guides/source \
  "$SITE_DIR/guides" \
  -E -a -v

# -------------------------
# Frontend (TypeDoc)
# -------------------------

cd frontend
npx typedoc --out ../"$SITE_DIR/frontend"
cd ..

# -------------------------
# Landing page
# -------------------------

cat > "$SITE_DIR/index.html" <<EOF
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Project Documentation</title>
  </head>
  <body>
    <h1>Project Documentation</h1>
    <ul>
      <li><a href="./backend/">Backend documentation</a></li>
      <li><a href="./guides/">Guides</a></li>
      <li><a href="./frontend/">Frontend documentation</a></li>
    </ul>
  </body>
</html>
EOF

touch "$SITE_DIR/.nojekyll"