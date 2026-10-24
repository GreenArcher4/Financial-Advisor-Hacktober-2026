# JENGA

> A financial buddy for Kenyan students: set a savings goal, get matched to a money market fund, and stay on track with M-Pesa nudges.

*Built at Hacktoberfest, Kiambu, powered by Gemma 4.*

*(Team and product name is a placeholder. Alternatives: Kibubu Labs, Weka Squad, Akiba Minds, Hacktober Hazina.)*

---

## The Problem

Most students receive money in lumps (HELB, pocket money, a gig) and it is gone before the month ends. Kenya's savings and investing rate is among the lowest in East Africa, at about 14% compared with 22% in Uganda and 36% in Tanzania.

Students aren't bad at saving. They lack simple, trustworthy guidance:

- Money market funds (MMFs) are a great first step, but there are dozens and the terms are confusing.
- Nobody tells a student which fund fits their situation.
- Online finance advice is either too technical, too salesy, or needs expensive data.

## The Solution

Kiota helps a student go from saving nothing to saving KES 500 a week, with a tool built for their reality.

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
| Goal and monthly contribution input | 🔲 |
| MMF matching engine (minimum deposit, access, risk) | 🔲 |
| M-Pesa (Daraja) saving reminders | 🔲 |
| CMA updates in simple language | 🔲 |
| Finance Q&A assistant (Gemma 4) | 🔲 |
| Swahili support | 🔲 |

*(Update these as you build: ✅ done, 🚧 in progress, 🔲 planned.)*

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

## Responsible AI and Compliance

- Kiota provides **education and fund comparison**. It does not hold user money or give personalised "buy this" investment advice.
- The assistant never invents yields. Fund figures come from a verified dataset and are always shown with an "as of [date]" label.
- When the assistant is unsure, it says so and points users to the fund manager or the CMA.
- Returns are never guaranteed, and disclaimers are shown in the app.
- Kenya's CMA is moving to license robo-advisory platforms, and its Regulatory Sandbox has been used by firms testing automated advice. Our path to launch is partnering with a licensed fund manager and/or applying to the sandbox.
- We follow the principles of Kenya's Data Protection Act, and on-device AI helps keep user data private.

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

## Our Edge

- Offline, on-device AI that works without data bundles
- Swahili and Sheng-friendly assistance
- Fund-neutral comparison across managers
- Student-first design: flexible amounts, a "skip this month" option, and emergency fund first
- Plain-language CMA updates that help students spot scams
- Built around M-Pesa from day one

## Roadmap

- [ ] Working demo with 3 to 5 real MMFs
- [ ] M-Pesa (Daraja) sandbox integration
- [ ] On-device Gemma 4 (E2B/E4B) assistant
- [ ] Swahili fine-tuning
- [ ] Streaks and goal progress tracking
- [ ] Group saving with friends
- [ ] Campus pilot (student clubs and chapters)
- [ ] Partnership with a licensed fund manager

## Tech Stack

*(Fill in what you actually use.)*

- **AI:** Gemma 4 (E2B/E4B on-device)
- **Payments:** Safaricom Daraja (M-Pesa)
- **Frontend:** _TBD_
- **Backend / data:** _TBD_

## Getting Started

```bash
# Clone the repository
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# Install dependencies
# (add your setup steps here)
```

## Team

| Name | Role |
|---|---|
| _Your name_ | _Role_ |
| _Teammate_ | _Role_ |

## License

Add a license, for example MIT or Apache 2.0.

---

*Built with ❤️ in Kiambu during Hacktoberfest 2026.*
