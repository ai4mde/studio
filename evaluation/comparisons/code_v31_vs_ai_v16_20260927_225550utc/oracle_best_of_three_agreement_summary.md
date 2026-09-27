# Oracle best of three: 40 cases

**POST-HOC ORACLE ANALYSIS — NOT DEPLOYABLE CANDIDATE-SELECTION PERFORMANCE**

AI-best is the maximum frozen AI score. Each Code dimension has its own best set among scorable candidates. The Code joint-best set is the intersection of the best sets for all applicable dimensions. Ties are retained. A dimension with D=0 is non-applicable; an applicable dimension with no scorable candidate blocks a joint-best finding.

- Cases: 40
- Unique AI-best cases: 22
- AI-tied-best cases: 18
- Cases with a Code joint-best candidate/set: 27
- Cases with no Code joint-best intersection: 13
  - Due to an applicable but unscorable dimension: 1
  - Due to dimension-best sets not intersecting: 12
- Cases with a tied Code joint-best set: 24
- Cases where an AI-best candidate belongs to the Code joint-best set: 24

For tied AI-best sets, agreement means at least one AI-best candidate is in the relevant Code-best set. The case table also records whether all AI-best candidates are in the Code joint-best set.

## AI-best overlap by Code dimension

| Dimension | Scorable cases | Cases with any AI-best overlap |
|---|---:|---:|
| Action | 40 | 31 |
| Flow | 40 | 30 |
| Control Node | 32 | 28 |
| Control Relation | 32 | 27 |

These are post-hoc oracle summaries and must not be interpreted as deployable automatic candidate selection performance.
