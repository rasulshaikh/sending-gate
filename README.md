# sending-gate

Pre-send quality gate for Clay outbound: PASS / FLAG / FAIL before Smartlead or HeyReach push.

This repo is the **open gate core**: validate rows, score them, then block or allow. Your production Clay table, enrichers, and private prompts live elsewhere. Point Clay (or a script) at this gate before the sequencer import step.

## Problem

Clay exports often look "done" while still carrying blank emails, placeholder copy, duplicate leads, or soft spam risks. Sequencers will happily send them. A thin, testable gate in front of Smartlead / HeyReach stops the obvious misses without locking you into one Clay workbook.

## Phases

1. **Validate** - schema, required fields, email shape, placeholders, dupes
2. **Score** - weighted quality score (0 to 100) from completeness + risk flags
3. **Block / allow** - map score and hard failures to `PASS` | `FLAG` | `FAIL`

Details: [`docs/WORKFLOW.md`](docs/WORKFLOW.md).

## How it fits a Clay export

```
Clay table (private) -> CSV/JSON export -> sending-gate -> allowed rows -> sequencer
```

- Keep enrichment and AI columns in your private Clay workflow.
- Export the minimum columns the gate expects (see workflow doc).
- Run the stub locally or wrap it in your own HTTP worker.
- Only rows with `PASS` (or accepted `FLAG`) go to Smartlead / HeyReach.

## Quick start (Python stub)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
python -m sending_gate examples/sample_rows.json
```

No API keys required. The stub scores local JSON only.

## Status labels

| Label | Meaning |
| --- | --- |
| PASS | Import allowed |
| FLAG | Human review before import |
| FAIL | Do not import |

## License

MIT. See [LICENSE](LICENSE).

## Topics

`gtm` `clay` `quality-gate` `outbound`
