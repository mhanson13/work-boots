# Lead Ingestion Flow (Zapier/Make/n8n)

## Trigger
- New GoDaddy contact form email in mailbox.

## Steps
1. Read email subject/body.
2. Map fields into webhook payload:
   - businessId
   - from
   - subject
   - textBody
   - htmlBody (optional)
   - messageId
   - receivedAt (ISO timestamp)
3. POST payload to `/webhooks/godaddy/email`.
4. If 201, notify owner via SMS/email.
5. If non-2xx, send failure alert to admin inbox.

## Retry policy
- Retry 3 times with exponential backoff (1m, 5m, 15m).
- Record dead-letter events for manual replay.
