# Security Policy

This public repository is a template and should contain only fictional sample data.

## Do Not Commit

- real customer names or account records;
- personal information;
- secrets, tokens, `.env` files, or credentials;
- private Google Workspace, CRM, BI, or ticket URLs;
- contract amounts, price tables, or non-public commercial terms;
- internal concerns that identify a real client or partner.

## Checks

Run these before publishing changes:

```bash
scripts/memory privacy-scan
scripts/memory lint
```

`privacy-scan` rejects unmasked email addresses and phone numbers. It is not a full data-loss-prevention system, so human review is still required.

## Reporting

If you find sensitive data in this public template, open a private security advisory or contact the maintainer directly. Do not include the sensitive value in a public issue.
