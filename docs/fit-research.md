# Research: better fitting of benchmark reference curves

Date: 2026-11-12

Implementation update: the recommended method is now available as the default
for `--fit-big-o` (`--metodo-fit log-baseline`). The original fit remains
available with `--metodo-fit ms`. The experiments below document the research
prototype that informed this change.

## Recommendation

Add an optional **log-space fit with a positive baseline**, using
`t(n) = a + c * f(n)` and keeping the documented complexity function `f`
fixed. Estimate `a` and `c` by minimizing
`sum((log(a + c*f(n_i)) - log(t_i))**2)`.

For these saved measurements, this gave the best leave-one-size-out error
among seven tested approaches. It improves the balance between the early
and late observations. It adds a parameter beyond the current single-scale
reference curve, so it is an explicitly named method. The research stage
itself did not change the production CLI; the subsequent implementation did.

It is not a complete solution to model mismatch. The brute-force reference
function is a loose upper bound, and its shape still differs from the
measured growth. A different numerical optimizer cannot remove that
difference while keeping the function fixed.

## Online sources and their implications

- [Hutter, Xu, Hoos and Leyton-Brown, Algorithm runtime prediction: Methods & evaluation](https://www.cl.cam.ac.uk/~ey204/teaching/ACS/R244_2025_2026/papers/hutter_ai_2014.pdf),
  Artificial Intelligence 206 (2014), section 3, uses log-transformed runtimes
  because runtimes on hard combinatorial problems vary substantially. This
  supports testing a log-residual objective for our many-orders-of-magnitude
  dataset. It does not establish our particular baseline model as optimal.
- [NIST: Accounting for Non-Constant Variation Across the Data](https://itl.nist.gov/div898/handbook/pmd/section4/pmd452.htm)
  describes transformation and weighting as approaches to unequal error
  variation, including logarithmic response transformations and validation
  in transformed coordinates. Neither approach is universally preferred.
- [NIST: Weighted Least Squares Regression](https://itl.nist.gov/div898/handbook/pmd/section1/pmd143.htm)
  discusses inverse-variance weighting and the importance of estimating
  weights reliably. Our relative-error candidate uses heuristic `1/t²`
  weights; these are not claimed to be reliably estimated inverse variances
  from the five repetitions.
- [SciPy: least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html)
  provides bounded nonlinear least squares and robust losses such as
  `soft_l1` and `huber`. Robust losses limit the influence of large residuals;
  the residual scale is an important choice. They do not repair an incorrect
  functional shape.

## Reproducible experiment

Input: `resultados/scipy-brute-1x1-10x10-mediana-5.json`. These are the original
five-run medians for SciPy and brute force at 1x1 through 10x10. No solver was
rerun, and no recorded time was replaced, smoothed or discarded.

The documented functions stay fixed:

- SciPy: `n²(m+n)`, which equals `2n³` on these square inputs.
- Brute force: `n(m+1)^n`.

Each function is normalized by its maximum log value for numerical stability.
This feature-only normalization does not use the held-out response and does
not change the model family. Every predicted time is positive.

Seven candidates were evaluated. Log-space baseline models use SciPy
`least_squares` with six starting points; the converged solution with the
lowest objective was retained. The robust candidates use `soft_l1` with
`f_scale=log(2)`, an illustrative factor-of-two residual scale rather than a
claim about the true noise distribution. Absolute-error baseline fitting
uses nonnegative least squares.

For validation, one complete input size is removed, the model is fitted on
the other nine sizes, and the omitted median is predicted. This is repeated
for all ten sizes. The error measure is
`exp(mean(abs(log(predicted / observed))))`: a symmetric average
multiplicative error factor. **1 is perfect; smaller is better.** It is not
a percentage or a statement that every point lies within that factor.

| Method | SciPy held-out factor | Brute-force held-out factor |
| --- | ---: | ---: |
| Current: squared error in ms, scale only | 3.439 | 28.214 |
| Relative squared error, scale only | 4.817 | 20.118 |
| Log-space squared error, scale only | 3.720 | 9.144 |
| Robust log-space error, scale only | 3.236 | 10.124 |
| Squared error in ms plus baseline | 3.503 | 547.636 |
| **Log-space squared error plus baseline** | **1.521** | **3.121** |
| Robust log-space error plus baseline | 1.527 | 3.398 |

Robust loss did not improve held-out results over the simpler log-space
baseline model here. Log transformation alone did not improve SciPy. Adding
a baseline while retaining absolute squared errors was particularly poor
for brute force: it estimated an 873 ms baseline, sacrificing the small
inputs. Both the objective and model need to suit the comparison.

## Early-point improvement and remaining trade-offs

For SciPy at 1x1, the current curve is about 105 times too small. The
log-space-baseline curve is about 1.31 times too small. For brute force at
1x1, the current curve is about 2,976 times too small; the candidate is about
2.34 times too large.

The candidate does worse at the largest point. On the full-data fit,
brute-force 10x10 is overpredicted by about 5.47 times, compared with about
1.002 times for the current fit, which is overwhelmingly anchored there.
When 10x10 is held out, the candidate overpredicts it by about 8 times,
compared with about 2.40 times for the current model. Thus the improvement
is in aggregate relative-error balance, not guaranteed accuracy at each
input or improved extrapolation of the largest runtime.

The fitted baseline is an empirical parameter and may absorb model mismatch;
it is not a direct measurement of function-call overhead. A reference curve
based on a theoretical upper bound cannot be expected to trace a measured
runtime distribution exactly. Closer forecasting would require separately
validated empirical models, potentially including graph/search features,
with labels distinct from the documented Big O reference functions.

## Limits and implementation guidance

- Only ten input sizes, two algorithms, one machine/session and a single
  fully connected, equal-score synthetic family were tested. These results
  are evidence for this dataset, not a universal ranking of fitting methods.
- Leave-one-size-out validation is small-sample evidence. Using it to select
  a method also introduces selection optimism. An independent benchmark
  collection is needed before claiming general predictive improvement.
- Keep objective choice independent of linear/log display scaling.
- Keep the current one-parameter method available and record the selected
  method, baseline, scale, objective, convergence and error measures in JSON.
- Do not quietly fit a free exponent or use an interpolating spline while
  labeling it as the same theoretical Big O function.
- Log objectives require positive measurements. Zero/below-resolution
  timings need an explicit policy; do not silently replace them with an
  arbitrary epsilon. This experiment rejected such inputs.
- Validate on BFS, Greedy, rectangular inputs and real filtered data before
  choosing a new project-wide default.

## Artifacts and checks

- Research runner: `tests/research_fit_methods.py`.
- Raw models, predictions, held-out results, source SHA-256 and library
  versions: `resultados/pesquisa-metodos-fit.json`.
- Comparison figure: `resultados/pesquisa-comparacao-fits.png`, generated by
  `tests/plot_fit_research.py`.
- The baseline predictions were independently checked against the current
  production fitter to relative tolerance `1e-12`.
- The candidate recovered known positive baseline and scale parameters on
  a noiseless synthetic control dataset.

The research scripts and generated artifacts follow the repository's existing
ignored-tests and ignored-results policies.
