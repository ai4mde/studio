# Action similarity pilot calibration

## Scope

This calibration uses only the 29 text-only rows from the frozen pilot whose
category is `equivalent` or `different` and whose `used_topology` value is
`no`. The frozen input checksum is
`5d0b01e8ed28032f7904c72d6a4e5517e82fc276f73f0d617f5d680b348494a1`.

Labels use the existing deterministic normalization in `eval_graph.py`:
Unicode NFKC, case folding, underscore/hyphen replacement, punctuation and
whitespace normalization, and trimming.

## Reproducible configuration

- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
- Similarity: cosine similarity of L2-normalized 384-dimensional embeddings
- Runtime: CPU with deterministic PyTorch algorithms and one thread
- Classification rule: predict equivalent when `similarity >= threshold`

After the pinned model has been downloaded once, reproduce the recorded output
without network access:

```bash
python -B -m evaluation.friedrich.calibrate_action_similarity \
  --model-cache /private/tmp/friedrich-hf-cache \
  --local-files-only \
  --recommended-threshold 0.44
```

## Pilot result

The best observed F1 plateau is `(0.42260495, 0.45036453]`. The representative
pilot threshold is `0.44`, which produces 19 TP, 2 FP, 0 FN, and 8 TN:
precision `0.9047619`, recall `1.0`, F1 `0.95`, and accuracy `0.93103448`.

The false positives are:

- `P018`: `Send Invoice` versus `receive invoice` (`0.91661161`)
- `P025`: `Create Order` versus `send order to supplier` (`0.56491393`)

These failures show that embedding similarity alone does not reliably preserve
action direction or process-stage distinctions. Therefore `0.44` is a pilot
recommendation, not a frozen final threshold. Freeze a final threshold only
after validating candidate generation and one-to-one matching on a separate
validation set, without changing the frozen pilot annotations.

## Artifacts

- `action_similarity_results.csv`: pair-level similarities and outcomes at
  `0.44`
- `action_threshold_results.csv`: every distinct threshold plateau
- `action_calibration_summary.json`: machine-readable configuration and result
