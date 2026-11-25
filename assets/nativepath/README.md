# NativePath article materials

Article measurements: 20 October 2026, run `20261020-124239-run`, release label `0.1.2`.
Current-code review: 21 October 2026; no new benchmark measurements introduced.

`measurements.json` is a plotting subset extracted from the retained run's client/server JSONL and event stream. It preserves three rounds and the full one-second soak tick series. Hostnames, network addresses, and response URLs are omitted. It is not the complete raw archive.

Generate the six figures with Python 3, Matplotlib, and NumPy:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install matplotlib numpy
python generate_figures.py
```

The script writes SVG, PNG, and PDF figures to the sibling `../images/nativepath/` directory.

The two flow diagrams (`secret-copies-client.svg`, `secret-copies-server.svg`) are conceptual, not measured. Each has a phone layout (`*-mobile.svg`) that the article serves below 640px. They come from a standard-library-only script:

```sh
python3 generate_secret_copies.py ../images/nativepath
```

The copy counts in the "usual Spring way" panels describe how those libraries typically handle the values. They are a lower bound, not the result of a scan.
Generation for this article used Matplotlib 3.11.2 and NumPy 2.5.4. All plotted data comes from the supplied archive, not those plotting-library versions.

Three dots show three observed rounds; connecting lines show arithmetic means, not confidence intervals. The direct client compares Java byte-array materialization against native-body handling. Spring adapters both return byte arrays. NativePath Rust allocations are outside the Java allocation counters.

The soak includes eight scan events (one retained-string control, seven protected scans). A descriptive association window begins one second before the inferred scan start and ends ten seconds after scan completion. Those windows contain 113 of 7,200 ticks, including all 27 with tick p99 above one second. They do not establish causation or a scan-free aggregate percentile.

The scan matrix reports recorded exact-byte marker matches. Controls intentionally retain Java strings. Sender status and output are not enforced by the under-load harness; negative scans alone do not prove successful injection or every intended failure transition.

Excluded: capacity comparisons, unverified Spring Netty identity, and unverified OpenSSL/BoringSSL provider comparisons.
