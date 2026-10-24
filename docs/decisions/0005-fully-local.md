# ADR-0005: 100% local — documents never leave the machine

- **Status:** accepted
- **Date:** 2026-10-24

## Context

The documents people convert are often private: contracts, medical records, internal reports,
unpublished theses. markitdown includes converters that depend on network services:

- `audio-transcription` (audio transcription), `youtube-transcription`;
- `az-doc-intel` and `az-content-understanding` (Azure);
- image description with an LLM;
- Wikipedia and Bing results converters, which work on URLs.

## Decision

ClearMD works **without a network**:

- the markitdown extras that use external services are not installed;
- no own converter makes network requests;
- the input is local files and folders; URLs are not accepted.

"Your documents never leave your machine" is a product feature and is stated in the README.

## Consequences

- **Gains:** verifiable privacy; works offline; no API keys or usage costs.
- **Costs:** there is no AI OCR, no audio transcription, and no conversion of web pages by URL. If any of these
  is ever added, it will be optional, disabled by default and come with a new ADR.

## Alternatives considered

- **Local by default, with optional network from now on:** rejected for now; it adds surface and configuration
  without a concrete need.
