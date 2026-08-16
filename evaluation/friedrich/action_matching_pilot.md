# Friedrich action-matching calibration pilot

## Scope

This pilot uses the human reference model and `run_1.json` generated artifact for
each selected case. It is only an action-label calibration set: gateway labels,
edge labels, flow correctness, and control-structure correctness are out of
scope.

The proposed pairs are recorded in `action_matching_pilot_pairs.csv`. The
`pilot_pair_group` values describe why a pair was sampled and must not be
treated as ground truth. The candidate list is intentionally targeted rather
than the Cartesian product of all reference and generated actions.

## Frozen calibration annotation set

The pilot annotations were frozen on 2026-08-14 for action-matching calibration.
The canonical file is `action_matching_pilot_pairs.csv`, with SHA-256:

`5d0b01e8ed28032f7904c72d6a4e5517e82fc276f73f0d617f5d680b348494a1`

The frozen set contains 35 reviewed pairs: 19 `equivalent`, 11 `different`,
2 `granularity_mismatch`, 1 `structurally_resolvable`, and
2 `unresolved_ambiguous`. The text-threshold calibration subset contains the
29 rows whose category is `equivalent` or `different` and whose
`used_topology` value is `no`: 19 positive and 10 negative examples.

Do not change these annotations or their governing categories during normal
model or threshold tuning. Any later correction must be justified as an
annotation error, documented explicitly, assigned a new freeze version and
checksum, and must not be made merely to improve similarity, matching, or F1
results.

## Selected cases

### 6-2 - inubit help/tutorial

Why selected: a short, sequential sanity-check case with concise labels. It
also tests an important directionality distinction (`send invoice` versus
`receive invoice`) and an action-granularity question (`create order` versus
`send order`).

Reference actions:

- `2120552530`: Send Invoice
- `2120552529`: Process Order
- `2120552527`: Receive Invoice
- `2120552525`: Create Order

Generated actions:

- `n1`: send order to supplier
- `n2`: process order
- `n3`: send invoice
- `n4`: receive invoice

### 5-2 - BizAgi vacation request

Why selected: a compact decision case with shared vocabulary across genuinely
different operations: submitting, approving, rejecting, notifying, and
returning a request. It tests whether similarity overweights the repeated words
`vacation` and `request`.

Reference actions:

- `2120553903`: Approve Vacation Request
- `2120553891`: Inform Reject Reason
- `2120553902`: Register Vacation Request
- `2120553879`: Verify Available Vacation Days
- `2120553889`: Make Administrative Task

Generated actions:

- `n1`: submit vacation request
- `n5`: approve request
- `n6`: notify HR
- `n7`: reject request
- `n8`: return application to employee

### 3-3 - Repetition/cycles

Why selected: a small loop case with repeated recommendation work. It provides
easy positive pairs and a hard distinction between checking, writing, and
revising the same recommendation.

Reference actions:

- `171`: Register Claim
- `174`: Examine Claim
- `179`: Check Recommendation
- `176`: Write Recommendation

Generated actions:

- `n1`: register claim
- `n2`: examine claim
- `n3`: write settlement recommendation
- `n7`: return claim to claims officer
- `n9`: revise settlement recommendation

### 6-3 - Powerlicht production planning

Why selected: the existing prototype case contains useful paraphrases, longer
labels, and repeated quality language. It also exposes possible partial matches
where one label omits information or represents a neighboring process step.

Reference actions:

- `44`: Produce Order
- `47`: Review Quality
- `26`: Determine Parts, Amounts and Delivery Date
- `27`: Transfer Data to PPS
- `29`: Procure Parts

Generated actions:

- `n1`: determine necessary parts and quantities
- `n2`: enter data into PPS
- `n3`: schedule production start
- `n7`: procure missing parts
- `n10`: recheck order quality

### 9-6 - Exercise 5 - electrical/physical design

Why selected: a parallel process with near-duplicate electrical and physical
branches. The reference contains two identically named `Review Previous Design`
actions, while the generated model adds the branch domain. This is the strongest
pilot for testing whether local structural context is needed to disambiguate
otherwise similar labels.

Reference actions:

- `16733726`: Test Physical Design
- `16733702`: Locate and Re-use Designs
- `16733721`: Review Previous Design (physical branch by topology)
- `16733744`: Test Electrical Design
- `16733743`: Update Electrical Design
- `16733742`: Review Previous Design (electrical branch by topology)
- `16733813`: Test Complete Design
- `16733736`: Update Physical Design

Generated actions:

- `n1`: locate and distribute relevant existing designs
- `n2`: send designs to the manufacturing process
- `n6`: review existing electrical designs
- `n7`: create electrical update plan
- `n8`: revise electrical design
- `n9`: test revised electrical design
- `n10`: review existing physical designs
- `n11`: create physical update plan
- `n12`: revise physical design
- `n13`: test revised physical design
- `n16`: initiate another design cycle

### 4-1 - Hajo Reijers intake workflow

Why selected: a long process with many related patient-file and meeting labels.
It exposes one-to-many granularity: the generated model combines planning and
conducting the first-intaker meeting, while the reference keeps them separate.

Reference actions:

- `2120552684`: Answer notice
- `2120552682`: Determine nursing officer
- `2120552681`: Record notice
- `2120552776`: Type out conversation
- `2120552758`: Meeting with second intaker
- `2120552732`: Assign intakers
- `2120552757`: Plan meeting first intaker
- `2120552731`: Close case
- `2120552734`: Hand out cards
- `2120552733`: Store assignment
- `2120552753`: Plan meeting second intaker
- `2120552724`: Ask for medical file
- `2120552725`: Update Patient file
- `2120552771`: Complete file with 2nd info
- `2120552695`: Create patient file
- `2120552699`: Store and print notice
- `2120552788`: Determine treatment
- `2120552768`: Complete file with 1st info
- `2120552767`: Meeting with first intaker

Generated actions:

- `n1`: notice patient need for mental treatment by telephone
- `n2`: inquire patient's name and residence
- `n3`: connect doctor to nursing officer
- `n4`: nursing officer inquires mental, health, and social state
- `n5`: record inquiry information on registration form
- `n6`: submit registration form to secretarial office
- `n7`: store registration form information in information system
- `n8`: create patient file for new patients
- `n9`: produce registration cards for first and second intaker
- `n10`: add new patient to list of new notices
- `n11`: assign patients to medical team at staff meeting
- `n12`: store assignment in information system
- `n13`: pass registration cards to intakers
- `n14`: prepare and send letter for medical file copy
- `n15`: plan and conduct first intaker meeting
- `n16`: record observations and standard checklist
- `n17`: add meeting notes to patient file
- `n18`: plan and conduct second intaker meeting
- `n19`: record observations using dictaphone
- `n20`: type and add information to patient file
- `n21`: formulate treatment plan

### 9-5 - Exercise 4 - expense reimbursement

Why selected: a decision-heavy process with several review/approval/payment
concepts and two generated actions with the identical label `reimburse to direct
deposit`. It tests shared vocabulary, neighboring-but-different activities, and
one-to-one handling of duplicate candidates.

Reference actions:

- `16733686`: Advise Employee to Start Again
- `16733655`: Send For Payment
- `16733673`: Transfer To Employee Account
- `16733639`: Review For Pre-Approval
- `16733689`: Approval In Progress Email
- `16733630`: Create Account
- `16733644`: Supervisor Review
- `16733660`: Notify Employee

Generated actions:

- `n1`: receive Expense Report
- `n2`: create new account if employee does not have one
- `n6`: automatically approve report under $200
- `n7`: reimburse to direct deposit
- `n9`: send rejection notice by email
- `n10`: reimburse to direct deposit
- `n13`: send 'approval in progress' email after 7 days
- `n14`: send cancellation notice and require resubmission after 30 days

## Manual review instructions

Review all 35 rows in `action_matching_pilot_pairs.csv`. For each row, set
`annotation_category` to exactly one of:

- `equivalent`
- `different`
- `granularity_mismatch`
- `structurally_resolvable`
- `unresolved_ambiguous`

Use the process meaning, not expected embedding behavior. `binary_match` is a
derived field and must not be entered independently: use `yes` for `equivalent`
or `structurally_resolvable`, `no` for `different` or
`granularity_mismatch`, and `excluded` for `unresolved_ambiguous` during
threshold calibration.

### Decision rule

1. Compare the normalized labels and their business meaning. If they describe
   clearly different operations, annotate `different`. Shared nouns alone are
   not evidence of equivalence; actor, object, direction, polarity, and outcome
   remain semantically relevant.
2. If one side combines multiple separately represented activities on the
   other side, annotate `granularity_mismatch`. Set `granularity_type` to
   `one_reference_to_many_generated` or
   `many_reference_to_one_generated`; the names state the direction explicitly.
3. If the labels describe the same operation and there is only one plausible
   occurrence-level correspondence, annotate `equivalent`.
4. If the labels are semantically plausible but multiple occurrence-level
   correspondences remain, inspect only the permitted local topology evidence.
   If it uniquely identifies this pair, annotate `structurally_resolvable`.
5. If permitted topology cannot identify a unique correspondence, annotate
   `unresolved_ambiguous`. Do not force a binary judgment.

Exact normalized equality normally establishes semantic plausibility, but it
does not by itself choose between repeated occurrences of the same action.
Repeated occurrences still require one-to-one disambiguation.

### Permitted topology evidence

Topology may be inspected only after the labels form a semantically plausible
candidate pair. Set `used_topology` to `yes` when any topology evidence affects
the decision, otherwise `no`. `topology_basis` may contain one or more of these
pipe-separated values:

- `nearest_matched_predecessor`
- `nearest_matched_successor`
- `same_branch`
- `loop_membership`
- `parallel_branch_membership`
- `decision_position`
- `reconvergence_position`

Use the nearest action nodes after transparent routing nodes are skipped. Do
not use global graph similarity, unrestricted path matching, or topology to
rescue semantically implausible labels. Record the concrete evidence in
`reviewer_notes` when `used_topology` is `yes`.

### Calibration and later binary scoring

Only `equivalent` and `different` rows are direct text-similarity calibration
examples. `structurally_resolvable` rows test the later tie-break policy and
must not be used to choose the text threshold. `granularity_mismatch` and
`unresolved_ambiguous` rows are also excluded from threshold selection.

For later strict one-to-one Action F1, `equivalent` and topology-confirmed
`structurally_resolvable` correspondences are eligible TPs. `different` pairs
are not matches. `granularity_mismatch` does not receive a complete TP or
partial credit and is reported separately. An unresolved item must be flagged
as unscorable under a predeclared policy; it must not be silently removed from
the final evaluation merely because it is difficult.
