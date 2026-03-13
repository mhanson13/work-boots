# Lead Intake Engine API

## Overview
What the API covers.

## Conventions
- JSON only
- ISO timestamps
- Status values
- Error format

## Endpoints

### POST /api/intake/manual
Purpose
Request body
Response body
Validation rules
Example request/response

### POST /api/intake/email
Purpose
Request body
Response body
Validation rules
Example request/response

### GET /api/leads
Purpose
Query params
Response body
Example

### GET /api/leads/{id}
Purpose
Response body
Example

### PATCH /api/leads/{id}/status
Allowed transitions
Request body
Response body
Example

### POST /api/leads/{id}/events
Purpose
Request body
Response body

### GET /api/leads/summary
Purpose
Response body
Example

## Error Responses
- 400 bad request
- 404 not found
- 409 invalid transition
- 500 internal error