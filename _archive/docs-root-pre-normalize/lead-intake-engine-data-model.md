# Lead Intake Engine Data Model

## Overview
What entities exist and how they relate.

## Entity Relationship Summary
businesses → leads → lead_events

## businesses
Field table:
- name
- type
- required
- description

## leads
Field table:
- name
- type
- required
- description

## lead_events
Field table:
- name
- type
- required
- description

## Status Enum
Allowed lead statuses

## Source Enum
manual, email, call, etc.

## Indexing / Uniqueness Suggestions
- lead submitted_at
- phone
- business_id + status
- dedupe support

## Deduplication Notes
How duplicate detection works

## Audit / History Notes
Why lead_events exists

## Future Tables
Optional later tables like:
- appointments
- notifications
- competitor_snapshots
- marketing_metrics