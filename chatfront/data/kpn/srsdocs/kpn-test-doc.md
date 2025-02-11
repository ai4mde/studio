---
id: kpn-test-doc
title: Test Document
description: A test document to verify markdown rendering and file access
date: 2024-01-01
---

# Test Document KPN group

## Features Overview

This document demonstrates various markdown features that our system supports.

### Code Blocks

Here's a TypeScript code example:

```typescript
interface User {
  id: string;
  username: string;
  group_name: string;
}

function getGroupDocuments(user: User): Promise<Document[]> {
  return fetchDocuments(user.group_name);
}
```

### Lists and Tables

Here are some key features:

- Syntax highlighting for code
- Table support
- List rendering
- Math equations (coming soon)

Priority levels:

1. High priority items
2. Medium priority items
3. Low priority items

Here's a feature comparison table:

| Feature | Status | Notes |
|---------|--------|-------|
| Markdown | ✅ | Fully supported |
| Code Highlighting | ✅ | Using rehype-pretty-code |
| Math Equations | 🚧 | In development |

### Blockquotes and Emphasis

> Important note: This is a test document to verify that our markdown rendering
> system is working correctly with the new file path structure.

Some text with **bold** and *italic* formatting, and even `inline code` blocks.

---

For more information, please refer to the documentation. 