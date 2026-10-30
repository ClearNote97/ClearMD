# Plan — Feature 012: Images in a folder

> Criteria: [`spec.md`](./spec.md). Decision: ADR-0033.

- `conversion/images.py`: `ImageSink`, `take_data_images`, `epub_images`.
- Converters take `images=` when asked (markitdown adapter, ODT, PDF); the worker builds the sink
  from `ConvertRequest.images` and returns `Converted.images`.
- `PlannedConversion.images` named in `run_batch(images=True)` with the catalog's suffix;
  `execution` writes them through `output_files.write_images`.
- Settings `images`; step 1, Settings, `--images`; tests first; screenshots; review; v0.7.0.
