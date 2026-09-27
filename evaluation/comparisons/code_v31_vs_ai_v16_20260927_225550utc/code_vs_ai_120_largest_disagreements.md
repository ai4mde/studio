# Largest Code versus AI rank disagreements

These are descriptive differences between related but non-identical constructs. Percentiles use average ranks for ties, calculated on each dimension's pairwise-complete candidates. A larger gap does not adjudicate either evaluator.

## Action

The five largest available rank gaps, including all ties at the cutoff, are shown. The full sortable table retains every candidate and every dimension.

### 5-4 / candidate_1 — rank gap 0.794117647059

- AI: overall 0.24, major severity, mixed_or_cascading. Most business actions are present, but the treasurer receipt-check is effectively duplicated/misgrouped, including an extra treasurer-check action after payment confirmation.
- Code Action: TP=11, FP=0, FN=0, scorable F1=1.0.
- Coverage/indeterminate context: Not applicable to Action; all Action facts are determinate.
- Likely source category: action alignment; semantic severity judgment.
- Descriptive reading: AI describes a duplicated or misgrouped treasurer check and gives a low holistic score; Code's Action ledger finds all eleven required action units and no Action FP. The holistic penalty also involves behavior outside Action F1. This does not adjudicate which evaluator is correct.

### 3-3 / candidate_1 — rank gap 0.773109243697

- AI: overall 1, none severity, none. The graph captures the required activities: examine the claim, write the settlement recommendation, check it, and repeat the recommendation on a Not OK outcome. The OK/Not OK marking and send-back are acceptably represented through the decision and retry loop rather than separate actions.
- Code Action: TP=3, FP=0, FN=3, scorable F1=0.6666666666666666.
- Coverage/indeterminate context: Not applicable to Action; all Action facts are determinate.
- Likely source category: action alignment; representation tolerance.
- Descriptive reading: AI accepts the OK/Not OK marking and send-back as implicit in the decision and retry path. Code reports three Action FN and ambiguous accepted anchors for those source units; the two observations use different action granularity. This does not adjudicate which evaluator is correct.

### 10-9 / candidate_2 — rank gap 0.722689075630

- AI: overall 1, none severity, none. The graph captures the request/change trigger, review, rejection or confirmation, execution of the measuring point change, and the two possible notifications with acceptable wording abstraction.
- Code Action: TP=5, FP=0, FN=3, scorable F1=0.7692307692307693.
- Coverage/indeterminate context: Not applicable to Action; all Action facts are determinate.
- Likely source category: action alignment; representation tolerance.
- Descriptive reading: AI accepts abbreviated wording of the measuring-point change process. Code records three unmatched required Action units and an ambiguous anchor; missing anchors also affect Code Flow. This does not adjudicate which evaluator is correct.

### 3-6 / candidate_1 — rank gap 0.722689075630

- AI: overall 0.4, major severity, wrong_loop_or_recurrence. Most main actions are present, but completeness checking is incorrectly duplicated and the required re-check after updated forms is not properly represented; severity evaluation is also unnecessarily duplicated across branches.
- Code Action: TP=6, FP=0, FN=0, scorable F1=1.0.
- Coverage/indeterminate context: Not applicable to Action; all Action facts are determinate.
- Likely source category: precedence interpretation; semantic severity judgment.
- Descriptive reading: Code finds every required Action unit. AI's low holistic judgment concerns duplicated checking and the incorrect return/recheck behavior, which Action F1 alone does not describe. This does not adjudicate which evaluator is correct.

### 3-6 / candidate_3 — rank gap 0.680672268908

- AI: overall 0.43, major severity, mixed_or_cascading. Most required business actions are present, but severity evaluation and forms-completeness checking are duplicated/misgrouped in ways that introduce unsupported repeated checking behavior.
- Code Action: TP=6, FP=0, FN=0, scorable F1=1.0.
- Coverage/indeterminate context: Not applicable to Action; all Action facts are determinate.
- Likely source category: precedence interpretation; semantic severity judgment.
- Descriptive reading: Code finds every required Action unit. AI's low holistic judgment concerns duplicated checking and the incorrect return/recheck behavior, which Action F1 alone does not describe. This does not adjudicate which evaluator is correct.

## Flow

The five largest available rank gaps, including all ties at the cutoff, are shown. The full sortable table retains every candidate and every dimension.

### 10-14 / candidate_2 — rank gap 0.710084033613

- AI: overall 0.4, major severity, wrong_branching_or_condition. The graph forces all four bill-examination actions into one fixed sequence before any confirm/reject outcome, introducing unsupported ordering among source cases and delaying the outcome until after all examinations.
- Code Flow: TP=8, FP=0, FN=0, scorable F1=1, D=8, I=0, coverage=1.0, official scalar status=official_numeric.
- Coverage/indeterminate context: All required facts in this dimension are determinate.
- Likely source category: precedence interpretation.
- Descriptive reading: Code marks all eight frozen required precedence facts TP. AI objects to extra fixed sequencing of alternative examinations before the outcome; that distinction is not expressed by the saved TP/FN counts alone. This does not adjudicate which evaluator is correct.

### 10-14 / candidate_3 — rank gap 0.680672268908

- AI: overall 0.42, major severity, wrong_branching_or_condition. The graph wrongly imposes a fixed sequence across all four examination actions before the outcome decision, adding unsupported precedence between source actions that are presented as separate conditional cases.
- Code Flow: TP=8, FP=0, FN=0, scorable F1=1, D=8, I=0, coverage=1.0, official scalar status=official_numeric.
- Coverage/indeterminate context: All required facts in this dimension are determinate.
- Likely source category: precedence interpretation.
- Descriptive reading: Code marks all eight frozen required precedence facts TP. AI objects to extra fixed sequencing of alternative examinations before the outcome; that distinction is not expressed by the saved TP/FN counts alone. This does not adjudicate which evaluator is correct.

### 3-3 / candidate_2 — rank gap 0.634453781513

- AI: overall 0.46, major severity, wrong_loop_or_recurrence. The required Not-OK sequence is not preserved: the graph does not correctly place return-to-claims-officer before the repeated recommendation, and it lacks the required path from a Not-OK outcome back into the repeat cycle.
- Code Flow: TP=3, FP=0, FN=0, scorable F1=1, D=5, I=2, coverage=0.6, official scalar status=official_null_indeterminate.
- Coverage/indeterminate context: Indeterminate facts may limit the Code observation.
- Likely source category: Code coverage/indeterminate handling; precedence interpretation.
- Descriptive reading: Code scores three determinate precedence facts TP while two of five required facts are indeterminate because of ambiguous Action anchors. AI diagnoses the Not-OK return and recurrence as defective. This does not adjudicate which evaluator is correct.

### 8-2 / candidate_1 — rank gap 0.621848739496

- AI: overall 0.47, major severity, wrong_loop_or_recurrence. Basic create/clarify→submit→post precedence is present, but the required correction→resubmission recurrence cannot be reliably matched because correction is not followed by a resubmission step and approval routing is inconsistent.
- Code Flow: TP=3, FP=0, FN=0, scorable F1=1, D=5, I=2, coverage=0.6, official scalar status=official_null_indeterminate.
- Coverage/indeterminate context: Indeterminate facts may limit the Code observation.
- Likely source category: Code coverage/indeterminate handling; precedence interpretation.
- Descriptive reading: Code scores three determinate precedence facts TP and leaves two of five indeterminate through ambiguous Action anchors. AI focuses on correction-to-resubmission recurrence and approval routing. This does not adjudicate which evaluator is correct.

### 10-9 / candidate_2 — rank gap 0.617647058824

- AI: overall 1, none severity, none. Required precedence is preserved: trigger/request before review, review before reject/confirm decision, confirmation before performing the change, and performance before success/failure notification.
- Code Flow: TP=3, FP=0, FN=3, scorable F1=0.6666666666666666666666666667, D=7, I=1, coverage=0.8571428571428571, official scalar status=official_null_indeterminate.
- Coverage/indeterminate context: Indeterminate facts may limit the Code observation.
- Likely source category: action alignment; Code coverage/indeterminate handling.
- Descriptive reading: Code records three Flow FN caused by missing required Action anchors and one indeterminate fact. AI accepts the high-level process order and the wording abstraction. This does not adjudicate which evaluator is correct.

### 5-2 / candidate_1 — rank gap 0.617647058824

- AI: overall 1, none severity, none. Required precedence is maintained: submit before supervisor receipt and decision; approval before HR notification and HR procedures; rejection before return to employee and review of rejection reasons.
- Code Flow: TP=1, FP=0, FN=1, scorable F1=0.6666666666666666666666666667, D=2, I=0, coverage=1.0, official scalar status=official_numeric.
- Coverage/indeterminate context: All required facts in this dimension are determinate.
- Likely source category: action alignment; precedence interpretation.
- Descriptive reading: Code marks one of two required Flow facts FN because its Action anchor is missing, despite complete Flow coverage. AI accepts the approval and rejection continuations in the graph. This does not adjudicate which evaluator is correct.

### 5-2 / candidate_2 — rank gap 0.617647058824

- AI: overall 1, none severity, none. Required precedence is maintained: submission before supervisor receipt, receipt before decision, and each branch follows the correct branch-specific action order.
- Code Flow: TP=1, FP=0, FN=1, scorable F1=0.6666666666666666666666666667, D=2, I=0, coverage=1.0, official scalar status=official_numeric.
- Coverage/indeterminate context: All required facts in this dimension are determinate.
- Likely source category: action alignment; precedence interpretation.
- Descriptive reading: Code marks one of two required Flow facts FN because its Action anchor is missing, despite complete Flow coverage. AI accepts the approval and rejection continuations in the graph. This does not adjudicate which evaluator is correct.

### 5-2 / candidate_3 — rank gap 0.617647058824

- AI: overall 1, none severity, none. Required precedence is preserved: submission precedes supervisor receipt and decision; approval precedes HR notification and HR procedures; rejection precedes return to employee and review of reasons.
- Code Flow: TP=1, FP=0, FN=1, scorable F1=0.6666666666666666666666666667, D=2, I=0, coverage=1.0, official scalar status=official_numeric.
- Coverage/indeterminate context: All required facts in this dimension are determinate.
- Likely source category: action alignment; precedence interpretation.
- Descriptive reading: Code marks one of two required Flow facts FN because its Action anchor is missing, despite complete Flow coverage. AI accepts the approval and rejection continuations in the graph. This does not adjudicate which evaluator is correct.

## Control Node

The five largest available rank gaps, including all ties at the cutoff, are shown. The full sortable table retains every candidate and every dimension.

### 5-2 / candidate_1 — rank gap 0.800000000000

- AI: overall 1, none severity, none. The approve/reject decision and branch membership are represented correctly, with appropriate continuation on each branch and termination after branch-specific handling. There is minor wording ambiguity about whether post-rejection review is optional, but the modeled routing is a reasonable reading of the text.
- Code Control Node: TP=0, FP=0, FN=1, scorable F1=0, D=1, I=0, coverage=1.0, official scalar status=official_numeric.
- Coverage/indeterminate context: All required facts in this dimension are determinate.
- Likely source category: control-node detection.
- Descriptive reading: AI accepts the approve/reject branch. Code does not match its one required logical Control Node; the three related Control Relation FN are downstream of that absent owner. This does not adjudicate which evaluator is correct.

### 5-2 / candidate_2 — rank gap 0.800000000000

- AI: overall 1, none severity, none. The graph correctly models the supervisor approval/rejection decision and routes to the appropriate approved and rejected continuations, both terminating appropriately.
- Code Control Node: TP=0, FP=0, FN=1, scorable F1=0, D=1, I=0, coverage=1.0, official scalar status=official_numeric.
- Coverage/indeterminate context: All required facts in this dimension are determinate.
- Likely source category: control-node detection.
- Descriptive reading: AI accepts the approve/reject branch. Code does not match its one required logical Control Node; the three related Control Relation FN are downstream of that absent owner. This does not adjudicate which evaluator is correct.

### 5-2 / candidate_3 — rank gap 0.800000000000

- AI: overall 1, none severity, none. The approve/reject branching is modeled correctly, with the approved path continuing to HR handling and the rejected path returning to the employee and then terminating; the extra merge on the approved path is semantically harmless.
- Code Control Node: TP=0, FP=0, FN=1, scorable F1=0, D=1, I=0, coverage=1.0, official scalar status=official_numeric.
- Coverage/indeterminate context: All required facts in this dimension are determinate.
- Likely source category: control-node detection.
- Descriptive reading: AI accepts the approve/reject branch. Code does not match its one required logical Control Node; the three related Control Relation FN are downstream of that absent owner. This does not adjudicate which evaluator is correct.

### 10-14 / candidate_2 — rank gap 0.642105263158

- AI: overall 0.4, major severity, wrong_branching_or_condition. The source describes conditional alternative invoice cases, each leading to examination and then confirmation or rejection. The graph incorrectly models them as one linear path with a single decision after all four examinations.
- Code Control Node: TP=1, FP=0, FN=0, scorable F1=1, D=1, I=0, coverage=1.0, official scalar status=official_numeric.
- Coverage/indeterminate context: All required facts in this dimension are determinate.
- Likely source category: control-node detection; semantic severity judgment.
- Descriptive reading: Code detects the one required decision node. AI's low holistic judgment concerns where the alternatives occur and how they route, beyond node presence. This does not adjudicate which evaluator is correct.

### 3-6 / candidate_1 — rank gap 0.642105263158

- AI: overall 0.4, major severity, wrong_loop_or_recurrence. The rejection branch is preserved, but the graph uses wrong decision placement and a wrong loop: incomplete forms lead to a separate success/retry decision, retry returns to informing again rather than re-checking, and success can reach registration without the mandated re-check of updated forms.
- Code Control Node: TP=3, FP=0, FN=0, scorable F1=1, D=3, I=0, coverage=1.0, official scalar status=official_numeric.
- Coverage/indeterminate context: All required facts in this dimension are determinate.
- Likely source category: control-node detection; precedence interpretation.
- Descriptive reading: Code matches all three required logical nodes. AI diagnoses wrong loop return and missing recheck, which depend on their relations and continuation rather than their mere presence. This does not adjudicate which evaluator is correct.

## Control Relation

The five largest available rank gaps, including all ties at the cutoff, are shown. The full sortable table retains every candidate and every dimension.

### 5-1 / candidate_1 — rank gap 0.778947368421

- AI: overall 1, none severity, none. The graph preserves the three-way alternative after assessment (approve, deny, or send to approver), merges those alternatives correctly, and then continues to customer feedback and termination.
- Code Control Relation: TP=0, FP=3, FN=3, scorable F1=0, D=3, I=0, coverage=1.0, official scalar status=official_numeric.
- Coverage/indeterminate context: All required facts in this dimension are determinate.
- Likely source category: control-relation semantics.
- Descriptive reading: AI regards the three alternatives and continuation as acceptable. Code marks each frozen relation FN+FP because its guard or branch target differs from the frozen fact. This does not adjudicate which evaluator is correct.

### 5-1 / candidate_2 — rank gap 0.778947368421

- AI: overall 1, none severity, none. The decision after risk assessment correctly models the three stated alternatives—approve, deny, or send to approver—and all branches properly continue to customer feedback before ending.
- Code Control Relation: TP=0, FP=3, FN=3, scorable F1=0, D=3, I=0, coverage=1.0, official scalar status=official_numeric.
- Coverage/indeterminate context: All required facts in this dimension are determinate.
- Likely source category: control-relation semantics.
- Descriptive reading: AI regards the three alternatives and continuation as acceptable. Code marks each frozen relation FN+FP because its guard or branch target differs from the frozen fact. This does not adjudicate which evaluator is correct.

### 5-1 / candidate_3 — rank gap 0.778947368421

- AI: overall 1, none severity, none. The graph preserves the intended exclusive outcomes after assessment: approve, deny, or send to approver, followed by continuation to customer feedback and termination.
- Code Control Relation: TP=0, FP=3, FN=3, scorable F1=0, D=3, I=0, coverage=1.0, official scalar status=official_numeric.
- Coverage/indeterminate context: All required facts in this dimension are determinate.
- Likely source category: control-relation semantics.
- Descriptive reading: AI regards the three alternatives and continuation as acceptable. Code marks each frozen relation FN+FP because its guard or branch target differs from the frozen fact. This does not adjudicate which evaluator is correct.

### 5-2 / candidate_1 — rank gap 0.778947368421

- AI: overall 1, none severity, none. The approve/reject decision and branch membership are represented correctly, with appropriate continuation on each branch and termination after branch-specific handling. There is minor wording ambiguity about whether post-rejection review is optional, but the modeled routing is a reasonable reading of the text.
- Code Control Relation: TP=0, FP=0, FN=3, scorable F1=0, D=3, I=0, coverage=1.0, official scalar status=official_numeric.
- Coverage/indeterminate context: All required facts in this dimension are determinate.
- Likely source category: control-node detection; control-relation semantics.
- Descriptive reading: AI accepts the approve/reject routing. Code marks the three relations FN because their owning required Control Node was not matched, so these FN are linked to node detection. This does not adjudicate which evaluator is correct.

### 5-2 / candidate_2 — rank gap 0.778947368421

- AI: overall 1, none severity, none. The graph correctly models the supervisor approval/rejection decision and routes to the appropriate approved and rejected continuations, both terminating appropriately.
- Code Control Relation: TP=0, FP=0, FN=3, scorable F1=0, D=3, I=0, coverage=1.0, official scalar status=official_numeric.
- Coverage/indeterminate context: All required facts in this dimension are determinate.
- Likely source category: control-node detection; control-relation semantics.
- Descriptive reading: AI accepts the approve/reject routing. Code marks the three relations FN because their owning required Control Node was not matched, so these FN are linked to node detection. This does not adjudicate which evaluator is correct.

### 5-2 / candidate_3 — rank gap 0.778947368421

- AI: overall 1, none severity, none. The approve/reject branching is modeled correctly, with the approved path continuing to HR handling and the rejected path returning to the employee and then terminating; the extra merge on the approved path is semantically harmless.
- Code Control Relation: TP=0, FP=0, FN=3, scorable F1=0, D=3, I=0, coverage=1.0, official scalar status=official_numeric.
- Coverage/indeterminate context: All required facts in this dimension are determinate.
- Likely source category: control-node detection; control-relation semantics.
- Descriptive reading: AI accepts the approve/reject routing. Code marks the three relations FN because their owning required Control Node was not matched, so these FN are linked to node detection. This does not adjudicate which evaluator is correct.
