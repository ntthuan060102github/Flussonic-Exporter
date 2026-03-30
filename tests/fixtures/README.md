# API response fixtures

## `flussonic_streams_response.json`

Synthetic payload used for **unit tests** and CI. It covers a minimal subset of `stats` (input, play, DVR, transcoder) so parsers and metric mapping stay aligned with the code.

## Capturing a real response (optional)

For regression against a **live** Flussonic server:

1. Call the same endpoint the exporter uses (HTTP Basic auth):

   `GET {scheme}://{host}:{port}/flussonic/api/v3/streams?limit=200`

2. Save the JSON response to a file **outside** the repo or under a path listed in `.gitignore` (do not commit secrets or customer data).

3. You can point a one-off test at that file locally (custom pytest or a small script) to validate parsing. Do **not** commit production credentials.

Keeping the **synthetic** fixture in git preserves reproducible CI; real captures are optional and operator-specific.
