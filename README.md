# JENGA

> A financial buddy for Kenyan students: set a savings goal, get matched to a money market fund, and stay on track with M-Pesa nudges.

*Built at Hacktoberfest, Kiambu, powered by Gemma 4.*

*(Team and product name is a placeholder. Alternatives: Kibubu Labs, Weka Squad, Akiba Minds, Hacktober Hazina.)*

---

## The Problem

Most students receive money in lumps (HELB, pocket money, a gig), and it is gone before the month ends. Students aren't bad at saving. They lack simple, trustworthy guidance:

- Money market funds (MMFs) are a great first step, but there are dozens and the terms are confusing.
- Nobody tells a student which fund fits their situation.
- Online finance advice is either too technical, too salesy, or needs expensive data.

## The Solution

Jenga helps a student go from saving nothing to saving KES 500 a week, with a tool built for their reality.

1. **Set a goal.** Tell us what you want to save (for example, "KES 20,000 for a laptop by June") and how much you can contribute each month.
2. **Get matched to an MMF.** We compare funds by minimum deposit, access to your money, and risk, and explain the match in plain language.
3. **Get M-Pesa nudges.** Receive a weekly or monthly prompt to save the amount you committed to.
4. **Stay informed.** Updates and notices from the Capital Markets Authority (CMA) of Kenya are turned into short, simple explainers.
5. **Ask anything.** Ask finance questions like "What's the difference between an MMF and a T-bill?" and get a clear answer in English or Swahili.

## Why Gemma 4?

Gemma 4 is open-weight under the Apache 2.0 license, and its small versions (E2B and E4B) are designed to run fully offline on phones.

- **No per-query API cost**, so the assistant stays free for students.
- **Privacy**: a student's financial data can stay on their device.
- **Works without internet**, which matters when data bundles run out.
- **Fine-tunable** for Swahili and everyday Kenyan phrasing.

## Features

| Feature | Status |
|---|---|
| Goal and monthly contribution input | ✅  |
| MMF matching engine (minimum deposit, access, risk) | ✅  |
| M-Pesa (Daraja) saving reminders | 🚧  |
| CMA updates in simple language | 🚧 |
| Finance Q&A assistant (Gemma 4) | 🔲 |
| Swahili support | 🔲 |

*(What each emoji means : ✅ done, 🚧 in progress, 🔲 planned.)*

## How It Works

```
Student inputs goal + monthly amount
            │
            ▼
   MMF matching engine  ◄── verified, dated fund data
            │
            ▼
   Gemma 4 explains the match in plain language
            │
            ▼
   M-Pesa (Daraja) prompts weekly / monthly
            │
            ▼
   Progress tracking + CMA updates + Q&A
```

> **Disclaimer:** Kiota is an educational tool and not a licensed financial advisor. Always confirm fund details with the fund manager before investing.

## Landscape

| Platform | Focus |
|---|---|
| Ndovu | Licensed investing app (MMF, stocks, bonds) |
| Hisa | Fractional stock investing |
| Chumz | Savings and goals app |
| Etica | MMF and unit trust transactions |
| Cashlet | Digital access to unit trusts |
| SC Shilingi / Sanlam | Bank-linked MMF transfers |
| Mali, Ziidi | M-Pesa-friendly MMF savings |
| General AI chatbots | Free Q&A, but no Kenyan fund data or M-Pesa |

**Where Kiota fits:** most of these are places where you invest. Kiota is a fund-neutral guide built for students that helps them choose and keeps them saving.

## Tech Stack

- **AI:** Gemma 4 (E2B/E4B on-device)
- **Payments:** Safaricom Daraja (M-Pesa sandboxing for now)
- **Frontend:** html, css
- **Backend / data:** python 

## Getting Started

```bash
# Clone the repository
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# Install dependencies
# (add your setup steps here)
```

## Team

| Name | 
|Samuel|
| Lorna | 
| CJ | 
| Aki| 

## License

coming soon

---


The Student Problem: "Most university students have KES 500 – KES 2,000 to save, but traditional banks offer less than 3% annual interest. They don't know which MMFs accept low minimums or how 15% withholding tax works."  
The Prompt:
Enter a query in your app: "I have KES 1,000 to invest today and can add KES 500 every month. Which MMFs can I join, and how much will I have in 1 year?"The Agent Action: Show Gemma 4 invoking compare_mmfs(1000) and calculate_net_returns(1000, 500, 12, 10.5) behind the scenes, then rendering a comparison table and net return projection directly on screen.

*Built during ❤️ Hacktoberfest Kiambu 2026.*
