# Migration notes

## `flussonic_stream_uptime_milliseconds`

The historical metric name `flussonic_stream_uptime_miliseconds` (typo: *miliseconds*) is still emitted **in addition to** `flussonic_stream_uptime_milliseconds` with the **same value**. Prefer the correctly spelled series in new dashboards and alerts; the old name may be removed in a future major release.

## Backward compatibility

- All other metric names from the baseline contract are unchanged unless listed here.
- See also [`compatibility.md`](compatibility.md) for aliases and policy.
