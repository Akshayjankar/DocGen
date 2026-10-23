import type { DocType } from "@/types/api";

export interface DocTemplate {
  id: string;
  title: string;
  docType: DocType;
  blurb: string;
  text: string;
}

export const TEMPLATES: DocTemplate[] = [
  {
    id: "incident-sop",
    title: "Incident Response SOP",
    docType: "sop",
    blurb: "Detect → contain → notify with a striped ownership table.",
    text: `# Purpose
Define how the team detects, contains and communicates a production incident.

# Scope
Applies to all customer-facing services and on-call engineers.

# Procedure
1. Acknowledge the alert within 5 minutes.
2. Open an incident channel and assign an incident commander.
3. Contain the impact: roll back, disable the feature flag or fail over.
4. Notify stakeholders within 15 minutes.
5. Publish a post-incident review within 3 working days.

Note: Never share customer data in the incident channel.

# Ownership
| Role | Owner | Responsibility |
| --- | --- | --- |
| Incident commander | On-call lead | Coordinates the response |
| Communications | Support manager | Customer and stakeholder updates |
| Scribe | Any engineer | Keeps the timeline |
`,
  },
  {
    id: "vpn-setup",
    title: "VPN Setup Guide",
    docType: "setup_guide",
    blurb: "Numbered steps, callouts and a code box for config snippets.",
    text: `# Before you begin
You need a company laptop and an active directory account.

# Install the client
1. Download the VPN client from the IT portal.
2. Run the installer and accept the defaults.
3. Restart your computer.

# Configure the connection
1. Open the client and choose Add profile.
2. Paste the gateway address below.

\`\`\`
gateway: vpn.example.com
protocol: ikev2
\`\`\`

Warning: Do not connect from untrusted public networks without MFA.

# Troubleshooting
- Connection times out: check your network and retry.
- Authentication fails: reset your password in the portal.
`,
  },
  {
    id: "q3-risk",
    title: "Q3 Risk Report",
    docType: "report",
    blurb: "Cover, revision history, auto TOC and themed headings.",
    text: `# Executive summary
Overall risk exposure decreased this quarter, driven by vendor consolidation.

# Key risks
## Vendor concentration
Two suppliers now account for most of our infrastructure spend.

## Regulatory change
New reporting rules take effect next quarter.

# Metrics
| Metric | Q2 | Q3 |
| --- | --- | --- |
| Open high risks | 9 | 6 |
| Mean time to mitigate (days) | 21 | 14 |

# Recommendations
- Add a third supplier for critical workloads.
- Complete the regulatory gap assessment by month end.
`,
  },
];

export function getTemplate(id: string): DocTemplate | undefined {
  return TEMPLATES.find((t) => t.id === id);
}
