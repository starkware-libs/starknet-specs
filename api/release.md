
# API Specification Releases

## Goal

Our goal is to allow collaboration on definition of the API specification for a StarkNet full node, while at the same time provide a reliable framework for understanding existing releases and ongoing work.
This document outlines how releases for the node API specification is managed and released.

## General Scheme

The api release follows a sequence of 3 phases: Draft -> Release Candidate (RC) -> Recommendation

Where the phases are defined as:

- Draft: the API specification is a work in progress, expect major changes and additions (types, methods added/changed/removed).
 - Generally there should be only one draft at a given time.
- Release Candidate:
 - Specification is ready to be implemented or has at least 1 implementation.
 - Expect minor changes. No addition/removal of methods.
 - There may be several release candidates (rc1, rc2, ...) with relevant changes.
- Recommendation: an agreed version of the specification, expected to be implemented and operated by nodes.

The tip of the master branch represents the current working draft.
Suggestions to API specification changes are made as pull requests on the master branch.

### Transition Between Phases
- Draft -> RC:
 - All changes from previous release discussed, no pending items.
 - No existing suggestions (PRs) for major changes.
- RC -> Recommendation:
 - A minimum of 7 working days passed from publication of latest release candidate.
 - No open discussion points.

## Version Numbering

Release follow a [semantic versioning](semver.org) for version tags.
We use `rc`_i_ ( i = 1,2,...) suffix to qualify different release candidates.
No suffix to a version means it's the recommendation version.

## Different Specification Documents

A release number is relevant to all API specification documents at the same time. In other words, they are all considered a single document.
Some parts of the API, e.g. the trace API, are considered optional. Still, they affect and adhere to the semantic version of the release.

## Technical Implementation

We use github releases on this repo to publish releases.

Git tags on the master branch signify releases.
Tags are structured as "v _major.minor.patch[-suffix]_"
where:
1. major, minor, patch are non negative integers as defined for semantic version.
2. _suffix_ is rc1,rc2, ...; qualifying release candidates.

Examples for tags:
- `v0.1.0-rc1`: release candidate 1 of version 0.1.0.
- `v1.0.0`: First recommended release of the API
- `v1.1.0-rc2`: 2nd release candidate for the release that has non-breaking changes over the first recommended release.



