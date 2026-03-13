# Lead Intake Flow

## Overview

This document defines the Phase 2 lead intake flow for **Work Boots Console**.

Its purpose is to describe how incoming GoDaddy contact form notification emails are processed into structured leads inside the system.

This flow is designed for small contractor businesses such as T&M Fire and Lars Construction, where fast response time is critical and the system must remain simple, reliable, and easy to maintain.

---

## Goal

Convert GoDaddy contact form notification emails into tracked leads with minimal friction.

The flow should:

- receive an email-based lead payload
- parse useful lead fields
- normalize the data
- deduplicate against recent leads
- create or update a lead
- record lead events
- trigger customer acknowledgment
- trigger contractor notification

---

## Scope

This document covers **Phase 2 only**.

Included in scope:

- email-based lead intake
- rules-based parsing
- lead normalization
- deduplication
- lead creation/update
- event recording
- mock notification triggering

Not included in scope:

- real GoDaddy APIs
- real inbox polling implementation
- Twilio production integration
- advanced workflow automation
- dashboard UI changes beyond lead visibility

---

## Assumptions

The Phase 2 flow assumes:

- contractor websites are hosted on GoDaddy Airo / Websites + Marketing
- GoDaddy sends contact form submissions by email
- Work Boots Console already has a Phase 1 backend with:
  - businesses
  - leads
  - lead_events
  - manual lead intake
  - lifecycle/status handling
- notification providers may still be mocked
- email parsing is rules-based, not AI-based

---

## High-Level Flow

```text
GoDaddy form submission
        ↓
Notification email generated
        ↓
Email payload received by Work Boots Console
        ↓
LeadParserService extracts fields
        ↓
Lead data normalized
        ↓
LeadDeduplicationService checks for duplicates
        ↓
Lead created or existing lead updated
        ↓
Lead events recorded
        ↓
Customer acknowledgment triggered
        ↓
Contractor notification triggered