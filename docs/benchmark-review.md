# Benchmark review — 2026-11-05

The suspicious example measured brute force at roughly 0.1161 ms for 2x2,
0.0168 ms for 3x3, and 0.0817 ms for 4x4. The review found an unnecessary
reference cycle in the brute-force solver, which can contribute to timing
spikes. It found no evidence of smaller inputs, an incomplete search, a
milliseconds conversion error, or graph points being swapped.

## Confirmed issue and fix

The nested recursive `visit` function captured the cell containing itself.
That cycle also retained references to the graph, best matching and trace
events after the solver returned. Their eventual reclamation could occur
inside a later timed solver call. A weak-reference test with cyclic GC
disabled failed against the original code, demonstrating the retention.

The solver now clears the recursive reference in a `finally` block after the
search. The same test passes with and without trace capture. Enumeration,
scoring, tie breaking and tracing are unchanged. Automatic GC remains enabled
and is neither forced nor suppressed by the benchmark.

The comparison loop also now drops each full solver result once its compact
diagnostics have been extracted, releasing the previous matrix before the
next solver starts. A weak-reference regression check verifies this lifetime.

The diagnostic script `tests/audit_benchmark.py` ran 100 sequences of sizes
1x1 through 6x6, with all four algorithms, in separate baseline and fixed
processes. Its `--baseline` mode loads `HEAD:app/matching.py` in memory without
changing workspace files. A wrapper and GC callbacks distinguish collections
inside the brute solver from collections during preparation/result building.

In this local audit, the baseline had 30 collections overall, including a
0.2439 ms collection inside a brute-force call. The fixed process had one
collection overall. These are observations from this run, not performance
guarantees: timing probes add some overhead and unrelated scheduling pauses
remain possible.

The original example was not instrumented, so its exact interruption cannot
be recovered. GC is a reproduced explanation consistent with that spike,
not a proven attribution of that particular data point.

## Search correctness

For a complete bipartite input with n origins and m destinations, the number
of valid partial and complete matchings is
`sum(comb(n, k) * perm(m, k), k=0..min(n,m))`.
Independent closed-form checks verify both the leaf count and the total
visited states, for sizes 1x1 through 7x7, plus 2x5 and 5x2, in both directions.

| Input | Visited states | Evaluated solutions | Pairs in the optimum |
| --- | ---: | ---: | ---: |
| 1x1 | 3 | 2 | 1 |
| 2x2 | 11 | 7 | 2 |
| 3x3 | 52 | 34 | 3 |
| 4x4 | 309 | 209 | 4 |

A separate oracle enumerates Cartesian products of assignments, rejecting
occupied destinations and blocked pairs. It checks cardinality and score
against both brute force and SciPy over 60 reproducible weighted/sparse
matrices, in both directions. This checks 240 brute-force/SciPy results and
120 BFS results; BFS is checked for maximum cardinality, since it does not
optimize the weights.

Diagnostic median solver times after the fix were approximately 0.0055,
0.0069, 0.0165, 0.0811, 0.5853 and 5.3036 ms for 1x1 through 6x6. The work
counts and these medians increase as expected. Individual wall-clock samples
need not increase, especially when the useful work takes only microseconds.
[Python's timing documentation](https://docs.python.org/3.12/library/timeit.html)
discusses interference from other processes and garbage collection.

## Benchmark and graph audit

- The command still executes each selected algorithm exactly once per size,
  with no warm-up, retries, smoothing or replacement of outliers. Repetition
  was used only in the separate diagnostic script.
- Each solver receives the exact requested dimensions and the same selected
  IDs/order for a given size. Insufficient database data fails before solving.
- Synthetic cases have every possible edge, with equal zero scores. MySQL
  cases retain their configured criteria and filters. Effective settings are
  now validated after CLI overrides, and unused synthetic settings are ignored
  consistently with the documented behavior.
- Timing boundaries enclose the selected solver and multiply elapsed seconds
  by 1000. Database reads, matrix/graph preparation, plotting, diagnostics
  export and console output are outside the plotted measurement.
- Solver-reported dimensions and finite, nonnegative times are now checked
  before accepting a point.
- A companion JSON stores the exact plotted float values, participant IDs,
  effective configuration, clock/environment metadata, pair counts and solver
  metrics. Brute-force state/solution counts also appear in the terminal.
- Plot tests verify exact Y-value mapping, including decreasing samples,
  unique colors, a legend below the axes and PNG/SVG/PDF export. The plot and
  command explicitly identify the limitations of one sample.

## Follow-up: BFS spike

The BFS loop has no recursive closure and the review found no equivalent
retention problem there. Its augmenting-path search was checked against the
independent oracle above, including blocked edges, rectangular inputs and
both directions. A focused test confirms that BFS moves an already allocated
developer to another task when an augmenting path is needed.

The existing internal edge-check counter is now exported as
`arestas_examinadas`, in the shared result metrics, terminal and JSON. On a
complete input with n origins and m destinations it equals
`sum(min(i, m), i=1..n)`. Formula checks cover square and rectangular cases
in both directions; with tracing enabled, the counter also agrees with the
number of edge-evaluation events.

A separate 100-sequence diagnostic run produced:

| Input | BFS edge checks | Median solver ms | Maximum observed ms |
| --- | ---: | ---: | ---: |
| 1x1 | 1 | 0.00440 | 0.00730 |
| 2x2 | 3 | 0.00485 | 0.01760 |
| 3x3 | 6 | 0.00520 | 0.00650 |
| 4x4 | 10 | 0.00590 | 0.00880 |

The work and median durations increase. The single 2x2 maximum exceeds the
single 4x4 maximum despite far less work. No GC callback occurred inside BFS
in this diagnostic run, so garbage collection cannot explain every outlier;
scheduling, interpreter and cache effects remain possible. The exact cause
of the earlier uninstrumented 3x3 spike is unknown. No BFS algorithm or
timing-boundary bug was found. These values are diagnostic observations,
not enforced ordering or an expectation that every future sample must rise.
Raw observations are in `resultados/revisao-bfs.json`.

## Validation limits

34 current benchmark/algorithm/API tests pass. The existing Bash forwarding
and menu check also passes. The broader local legacy test file still targets
removed `ssp`/`kwok` algorithms and missing old APIs, as identified before this
review. Live MySQL/Compose verification could not run because Docker is stopped;
the database selection path was checked with controlled data and mocked reads.

Local diagnostic reports are in `resultados/revisao-antes.json` and
`resultados/revisao-depois.json`; these generated files follow the project's
existing ignored-results policy. The local test/diagnostic scripts likewise
follow the existing ignored-tests policy.
