# Purpose

Describe the password reset process for support staff.

## Scope

All customer support engineers.

## Roles

Support Lead owns this procedure.

## Procedure

1. Verify the requester identity using two factors.
2. Open the admin console and locate the account.
3. Reset the password and notify the user securely.

## Records

Record the ticket ID and timestamp in the audit log.

Warning: Do not email passwords in plaintext.

```bash
sudo passwd alice
```
