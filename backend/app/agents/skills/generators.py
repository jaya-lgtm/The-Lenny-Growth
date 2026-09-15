import re
from typing import Dict, Any, List, Optional
from app.agents.schemas import SourceCitation


def sanitize_html_content(raw_html: str) -> str:
    """
    Sanitizes generated HTML to ensure it can be safely rendered in a sandboxed iframe.
    Removes dangerous external scripts, cookies, parent/top navigation, and form hijacking.
    """
    # Remove script tags that load external origins
    sanitized = re.sub(r'<script\s+[^>]*src=["\']http[^"\']+["\'][^>]*>.*?</script>', '', raw_html, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'<script\s+[^>]*src=["\']//[^"\']+["\'][^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    # Neutralize parent/top window navigation attempts and document access
    sanitized = re.sub(r'(window\.)?(top|parent)\.(location|document)', '/* blocked */', sanitized, flags=re.IGNORECASE)
    # Remove meta refresh tags
    sanitized = re.sub(r'<meta\s+[^>]*http-equiv=["\']refresh["\'][^>]*>', '', sanitized, flags=re.IGNORECASE)
    # Remove base tags
    sanitized = re.sub(r'<base\s+[^>]*>', '', sanitized, flags=re.IGNORECASE)
    # Neutralize target="_top" and target="_parent"
    sanitized = re.sub(r'target=["\'](_top|_parent)["\']', 'target="_blank"', sanitized, flags=re.IGNORECASE)
    # Neutralize external form actions
    sanitized = re.sub(r'<form\s+[^>]*action=["\']http[^"\']+["\']', '<form action="#"', sanitized, flags=re.IGNORECASE)

    # Ensure valid document structure and baseline sandboxed styles
    if "<!DOCTYPE html>" not in sanitized and "<html" not in sanitized:
        sanitized = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 1.5rem;
      color: #1e293b;
      background: #f8fafc;
      line-height: 1.5;
    }}
  </style>
</head>
<body>
{sanitized}
</body>
</html>"""
    return sanitized



def generate_mock_artifact(
    mode: str,
    query: str,
    citations: List[SourceCitation],
) -> Dict[str, Any]:
    """
    Generates deterministic, high-fidelity artifacts for testing and offline execution.
    Every artifact directly references the provided real ChatPRD citations.
    """
    primary_source = citations[0] if citations else None
    guest = primary_source.guest if primary_source and primary_source.guest else "Lenny's Podcast Experts"
    title_src = primary_source.title if primary_source else "Product Growth Frameworks"
    url_src = primary_source.source_url if primary_source else "https://www.youtube.com"
    rel_path = primary_source.relative_path if primary_source else "episodes/transcript.md"

    if mode == "growth_action_plan":
        title = f"Growth Action Plan: {query.strip().title()[:60]}"
        content = f"""# 🚀 Growth Action Plan: {query.strip().title()}

**Executive Owner:** Head of Growth / Lead Product Manager  
**Primary Evidence Grounding:** [{title_src}]({url_src}) featuring **{guest}** (`{rel_path}`)  
**Evaluation Cadence:** 90-Day Milestones

---

## 1. Problem Statement & Baseline Diagnosis
* **Core Problem:** New users experience drop-off prior to discovering the primary value proposition.
* **Target Metric:** 30-day retention curve plateau and core activation rate.
* **Grounding Evidence:** As emphasized by **{guest}**, sustainable retention requires eliminating cognitive friction during the initial user onboarding sequence while preserving intentional friction that customizes user setup.

---

## 2. Phased Implementation Roadmap

### Phase 1: Days 1–30 (The Setup Moment)
- [ ] Audit user onboarding flow to identify unnecessary form fields and configuration steps.
- [ ] Deploy workspace invite flow during the onboarding wizard.
- [ ] Instrument funnels tracking time-to-first-value (TTFV) across cohorts.
- [ ] **Expected Impact:** +12% increase in completed setups.

### Phase 2: Days 31–60 (The Aha! Moment)
- [ ] Deliver contextual empty states guiding new users to their first core action.
- [ ] Introduce interactive in-product templates based on user persona selection.
- [ ] Run A/B test on onboarding checklists vs. passive tours.
- [ ] **Expected Impact:** +18% lift in users reaching the aha milestone.

### Phase 3: Days 61–90 (The Habit Moment)
- [ ] Trigger behavioral re-engagement notifications tied to natural product cadence.
- [ ] Establish weekly summary digests reinforcing value received.
- [ ] Review retention curves for flattening at Day 30 and Day 60.
- [ ] **Expected Impact:** Flattening cohort curves with +8% sustained retention.

---

## 3. Risks, Assumptions & Mitigation
| Risk | Probability | Mitigation Strategy |
| :--- | :--- | :--- |
| Onboarding friction reduces initial signups | Medium | Implement progressive profiling post-signup |
| In-app checklist fatigue | Low | Limit checklist to 3 high-impact milestones |
| Premature monetization drop-off | High | Gate advanced features only after value realized |

---

## 4. Evidence Traceability & Grounding
* **Transcript Source:** `{title_src}`
* **Guest Insights:** {guest}
* **Repository Path:** `{rel_path}`
* **Video Reference:** [{url_src}]({url_src})
"""
        content_format = "markdown"

    elif mode == "ship30_essay":
        title = f"Why Most Growth Advice Fails: The Power of Compounding Activation Loops"
        # Generate an essay strictly meeting the 1,000 - 1,500 word target (body: ~1,280 words, total: ~1,335 words)
        content = f"""# {title}

### By Product & Growth Insights | Grounded in conversations with {guest}

Most early-stage startups obsess over the wrong growth metric. Founders and product leaders routinely pump capital into top-of-funnel acquisition, celebrate cosmetic signup spikes, and wonder why 85% to 90% of their new signups evaporate before Day 7.

The fundamental reality of product growth is simple: sustainable growth is almost never an acquisition problem—it is nearly always an activation and retention problem. If users do not rapidly experience the core value proposition of your product in their initial session, all subsequent marketing spend is merely subsidizing a leaky bucket.

In our review of Lenny's Podcast with **{guest}** (discussing *{title_src}*), the operational lesson is unequivocal: sustainable, compounding growth requires orchestrating micro-interactions around guiding users through a disciplined sequence of behavioral milestones. When you treat onboarding not as a series of tooltip carousels, but as a deliberate cognitive transformation, your retention curve flattens and your growth engine turns into a self-sustaining loop.

Here is the three-part playbook top product and growth teams use to build enduring, high-velocity growth loops.

---

## Part 1: The Three Irreducible Milestones of User Activation

Product teams frequently make the mistake of treating onboarding as a mechanical checklist—prompting users through generic tours, modals, and permission requests. However, genuine user activation is psychological. It requires ushering users across three distinct thresholds:

### 1. The Setup Moment: Intentional Friction vs. Cognitive Abandonment
The Setup Moment encompasses the minimum configuration necessary for the product to deliver value. For Slack or Linear, it means creating a workspace and adding at least one project or teammate. For Loom, it means installing the extension and granting media permissions. For an analytics platform, it means dispatching the first event beacon.

The primary anti-pattern here is confusing necessary setup with administrative data entry. When teams ask new users to fill out twenty form fields before seeing the interface, abandonment rates skyrocket. Conversely, eliminating all friction entirely can leave new users staring at a barren, empty canvas.

The strategic solution is *intentional friction*. Ask for only the critical inputs required to customize the initial experience, while deferring non-essential preferences until after the user has tasted success.

### 2. The Aha! Moment: The Emotional Inflection of Value Realization
The Aha! Moment represents the precise threshold where the user first feels the promised value in their gut. It is not merely the mechanical completion of an onboarding tour; it is the subjective experience of relief, delight, or productivity.
- For Zoom, it is when a meeting connects in two seconds without forcing the participant to register an account or install heavy software.
- For Dropbox in its early days, it was dropping a file into a local operating system folder and witnessing the green sync checkmark appear instantly.
- For Figma, it was sending a browser link to a colleague and seeing their multiplayer cursor move in real-time across the design canvas.

As **{guest}** points out, elite product organizations map every friction point in the user journey and ruthlessly eliminate any obstacle between initial signup and this emotional epiphany. If your time-to-aha exceeds five minutes in self-serve SaaS, your drop-off curve will resemble a cliff.

### 3. The Habit Moment: Anchoring Core Value into Natural Usage Cadence
Reaching the aha moment once is an accomplishment, but it does not guarantee long-term retention. The Habit Moment occurs when the product successfully binds itself to the user's recurring behavioral triggers.

Every product has a natural usage cadence dictated by the problem it solves. An enterprise communication tool operates on a daily cadence; a sprint board operates on a weekly cadence; an invoicing system operates on a monthly cadence. 

A frequent founder mistake is attempting to force an unnatural frequency upon users. Pushing daily notifications for an accounting product does not build a habit—it causes immediate unsubscribes. Success requires identifying the user's real-world trigger and providing recurring reinforcement each time that trigger fires.

---

## Part 2: Why Linear Funnels Are Obsolete (And Why Compounding Loops Win)

Traditional marketing frameworks condition teams to view product growth through the lens of a linear funnel: Awareness → Acquisition → Activation → Retention → Revenue → Referral.

While funnels remain useful for diagnosing point-in-time friction at individual steps, their structural flaw is severe: funnels are non-compounding. To generate twice as much revenue at the bottom of a linear funnel, you must continually pour twice as much money or ad spend into the top. The moment paid acquisition budgets contract, top-of-funnel growth stalls and company expansion grinds to a halt.

Category-defining businesses rely instead on **compounding growth loops**. In a growth loop, the output from a single cohort of activated users becomes the direct input that acquires and activates the subsequent cohort:

1. **Viral & Collaborative Loops**: A designer creates an interactive prototype in Figma and shares a preview with teammates. The recipients sign up to leave comments and inspect CSS properties. Those teammates subsequently create their own project boards and invite their teams, propagating an exponential acquisition wave.
2. **User-Generated Content (UGC) Loops**: A user asks an insightful technical question on Stack Overflow or writes a guide. Search engines crawl and index the high-quality content. Future practitioners search for answers on Google, land directly on the page, extract value, and create accounts to contribute their own solutions.
3. **Paid Reinvestment Loops**: Paid acquisition channels acquire paying customers whose high activation and retention yield a healthy Customer Lifetime Value (LTV). The gross margin generated from these cohorts is systematically reinvested into acquiring more paid traffic within a strict payback window.

When your activation efficiency improves, loop velocity accelerates. A 15% increase in core activation does not merely produce a one-time step function in revenue; it compounds multiplicatively through every subsequent iteration of your viral, content, and reinvestment engines.

---

## Part 3: The 4-Step Operational Framework for Growth Teams

Translating these strategic growth insights into measurable tactical execution requires a systematic, evidence-grounded framework:

1. **Quantify Your North Star Activation Milestone**: Perform rigorous cohort regression analysis to identify the exact behavioral threshold that distinguishes retained users from churned users at Day 30 and Day 90. Avoid vague intuition. Define the metric with mathematical precision.
2. **Audit and Eradicate Toxic Cognitive Friction**: Map every screen, input field, and confirmation dialog in your existing signup sequence. Remove mandatory email verification prior to first-use wherever fraud risks permit. Eliminate unnecessary password complexity barriers, and defer demographic questionnaires until after the first aha moment.
3. **Deploy High-Leverage Scaffolding and Role-Based Templates**: Never subject a newly activated user to an intimidating blank canvas. Provide interactive starter kits, role-specific templates, and pre-populated sample workspaces that allow the user to visualize the end-state of the product immediately upon first login.
4. **Inspect Cohort Retention Curves Weekly**: Discontinue reporting on blended aggregate retention. Segment user cohorts by week and month of signup, plotting their retention percentages over time. A healthy product is diagnosed when the tail of the cohort curve flattens horizontally—proving enduring product-market fit.

---

## Key Takeaways to Remember

- **Activation is the foundational prerequisite for retention**: If a user never experiences the aha moment, they cannot form a behavioral habit, rendering retention efforts futile.
- **Intentional friction triumphs over zero friction**: Eliminate administrative burdens, but strategically incorporate necessary setup questions that tailor and accelerate immediate value delivery.
- **Compounding loops consistently outcompete linear funnels**: Build sustainable mechanisms where active product usage inherently generates new user discovery, collaboration, and content.
- **Empirical evidence must anchor growth execution**: As emphasized by **{guest}**, growth is neither luck nor speculative hacking—it is a disciplined engineering discipline centered on metric precision, systematic experimentation, and sustainable compounding loops.

---

## Evidence Traceability & Grounding
* **Transcript Source:** `{title_src}`
* **Featured Guest:** {guest}
* **Corpus Reference Path:** `{rel_path}`
* **Direct Video Evidence:** [{url_src}]({url_src})
* **Methodological Distinction:** Transcript-supported findings reflect actual episode dialogue, while implementation frameworks represent actionable strategic recommendations.
"""
        content_format = "markdown"


    elif mode == "checklist":
        title = f"Audit Checklist: {query.strip().title()[:60]}"
        content = f"""# 📋 Growth Audit Checklist: {query.strip().title()}

**Auditor:** Growth Product Team  
**Grounded in:** [{title_src}]({url_src}) with **{guest}**  
**Corpus Traceability:** `{rel_path}`

---

### Section 1: User Onboarding & Setup Readiness
- [ ] **1.1 Frictionless Authentication**: Signup available via single-click Google/SSO without mandatory phone/email verification delay.
- [ ] **1.2 Progressive Profiling**: Maximum of 2 setup questions (Role, Primary Goal) asked upfront; secondary metadata requested in-context later.
- [ ] **1.3 Teammate Invitation**: Collaborative invite link accessible during setup with pre-formatted permissions.
- [ ] **1.4 Time-to-First-Value (TTFV)**: First core action reachable within 60 seconds of clicking 'Sign Up'.

### Section 2: Value Delivery & The Aha! Moment
- [ ] **2.1 High-Quality Default Templates**: Pre-populated workspaces available so users never encounter an intimidating blank state.
- [ ] **2.2 In-Context Action Guidance**: Interactive checklist guiding the user to the core value proposition.
- [ ] **2.3 Success Confirmation Feedback**: Clear visual confirmation and celebration when the first core milestone is achieved.

### Section 3: Habit Formation & Re-engagement
- [ ] **3.1 Cadence-Matched Notifications**: Re-engagement emails triggered only when users fall behind their natural usage rhythm.
- [ ] **3.2 Value Summary Digest**: Weekly email summarizing time saved, tasks completed, or metrics achieved.
- [ ] **3.3 Unsubscribe Transparency**: One-click preference center to prevent notification fatigue and spam complaints.

### Section 4: Metrics & Cohort Instrumentation
- [ ] **4.1 Funnel Tracking**: Instrumented events for `signup_started`, `setup_completed`, `aha_moment_reached`, `habit_active`.
- [ ] **4.2 Cohort Curve Dashboard**: Weekly retention curves monitored for flattening between Day 14 and Day 60.
- [ ] **4.3 Drop-off Heatmap**: Monthly drop-off audits on the onboarding funnel steps.

---

*Verified against transcript insights from **{guest}** (`{rel_path}`).*
"""
        content_format = "markdown"

    elif mode == "framework":
        title = f"Strategic Framework: {query.strip().title()[:60]}"
        content = f"""# 📐 Strategic Growth Framework: {query.strip().title()}

**Source Authority:** **{guest}** (*{title_src}*)  
**Relative Path:** `{rel_path}` | **Video URL:** [{url_src}]({url_src})

---

## 1. Conceptual Framework Matrix

```
                HIGH NATURAL CADENCE (Daily / Weekly)
                         │
        [Habit Loops]    │    [Collaborative Viral Loops]
      Slack, Notion      │    Figma, Miro, Zoom
                         │
─────────────────────────┼─────────────────────────
                         │
      [Content SEO Loops]│    [Paid Reinvestment Loops]
      Zapier, Canva      │    Wealthfront, Ramp
                         │
                LOW NATURAL CADENCE (Monthly / Annual)
```

## 2. Core Operating Principles
1. **Match Acquisition Loop to Product Cadence**:
   - Products with high natural collaboration (e.g. Figma, Zoom) should invest in **collaborative invite loops**.
   - Products with lower natural frequency (e.g. Tax, Real Estate) must leverage **SEO, content, or paid loops**.
2. **Flattening Before Scaling**:
   - Never scale paid acquisition until cohort retention curves demonstrate a flat horizontal tail (indicating product-market fit).
3. **Intentional Setup Friction**:
   - As emphasized by **{guest}**, high-retention onboarding balances low friction with high intentionality.

## 3. Decision Tree for Growth Teams
```
Does your product have multi-player utility?
├── YES ➔ Prioritize Collaborative In-Product Loops (Invite teammates to view/edit)
└── NO ➔ Does user activity generate public content or indexable pages?
    ├── YES ➔ Prioritize Content & SEO Loops (Public templates, user profiles)
    └── NO ➔ Focus on Paid Reinvestment Loops & Direct Referral Incentives
```
"""
        content_format = "markdown"

    elif mode == "experiment_plan":
        title = f"Experiment Plan: {query.strip().title()[:60]}"
        content = f"""# 🧪 Experiment Plan: {query.strip().title()}

**Owner:** Growth Experimentation Lead  
**Evidence Source:** [{title_src}]({url_src}) featuring **{guest}** (`{rel_path}`)

---

## 1. Hypothesis & Objective
* **Hypothesis:** If we replace the generic blank welcome screen with three interactive, role-specific templates during onboarding, then new user activation will increase by **+15%** because users can immediately experience the core aha moment without manual configuration.
* **ICE Priority Score:**
  - **Impact:** 8/10 (Directly affects initial cohort activation)
  - **Confidence:** 8/10 (Validated by transcript benchmarks from {guest})
  - **Ease:** 7/10 (Templates already built; requires wizard integration)
  - **Overall ICE Score:** **7.7 / 10**

---

## 2. Experiment Design & Variants
* **Audience:** 100% of new self-serve signups, randomized 50/50.
* **Duration:** 14 days (Minimum sample size: 4,000 signups per variant for 95% statistical power).

| Variant | Experience Description |
| :--- | :--- |
| **Control (50%)** | Existing flow: Users land on an empty workspace with a tooltip pointing to 'New Project'. |
| **Treatment (50%)** | New flow: Users are presented with 3 clickable template cards ('Sprint Planning', 'Roadmap', 'Bug Tracking') pre-loaded with sample data. |

---

## 3. Metrics Matrix
* **Primary Success Metric:** Activation Rate (reaching the core milestone within 24 hours of signup).
* **Secondary Metrics:**
  - Onboarding completion rate
  - Day-7 retention rate
  - Support ticket volume for 'how to get started'
* **Guardrail Metric:** Day-1 signup drop-off rate (must not increase by more than 1%).

---

## 4. Rollout & Decision Criteria
* **Ship Condition:** Statistically significant (p < 0.05) lift of >= 8% on primary metric with neutral or positive guardrails.
* **Kill Condition:** Significant drop in Day-1 retention or negative feedback on template clutter.
"""
        content_format = "markdown"

    elif mode == "strategy_doc":
        title = f"Growth Strategy Document: {query.strip().title()[:60]}"
        content = f"""# 📊 Growth Strategy Document: {query.strip().title()}

**Document Version:** 1.0 (Final)  
**Executive Sponsor:** Head of Growth  
**Transcript Evidence Base:** **{guest}** in [{title_src}]({url_src}) (`{rel_path}`)

---

## Executive Summary
This document establishes the strategic growth roadmap for scaling product activation, retention, and compounding loops. Based on real-world transcript insights from {guest}, our priority is shifting focus from linear top-of-funnel acquisition to sustainable cohort retention and self-reinforcing product loops.

---

## Strategic Pillars

### Pillar 1: Onboarding Friction Rationalization
* **Objective:** Shorten time-to-first-value (TTFV) from 12 minutes to under 3 minutes.
* **Tactics:**
  - Implement single-click template instantiation.
  - Defer non-critical setup steps (billing, profile pictures, advanced integrations) until Day 3.

### Pillar 2: Cohort Retention Stabilization
* **Objective:** Establish a permanent retention floor of >= 35% on Day 60.
* **Tactics:**
  - Introduce behavioral milestone notifications based on actual user progression.
  - Build automated re-activation loops for dormant workspaces.

### Pillar 3: Product-Led Growth Loops
* **Objective:** Drive 40% of new monthly user acquisitions organically via in-product loops.
* **Tactics:**
  - Launch collaborative guest viewer seats.
  - Publish public templates indexed by Google search.

---

## Governance & Review Cadence
* **Weekly:** Growth experiment velocity reviews (target: 3 experiments shipped / week).
* **Monthly:** Cohort curve and retention plateau audits.
* **Quarterly:** Strategic pillar review and benchmark alignment against Lenny's Podcast guest metrics.
"""
        content_format = "markdown"

    elif mode == "html_css":
        title = f"Interactive Component: {query.strip().title()[:60]}"
        raw_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Growth Loop & Activation Visualizer</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 24px;
      background: #0f172a;
      color: #f8fafc;
    }}
    .card {{
      background: #1e293b;
      border-radius: 12px;
      padding: 24px;
      border: 1px solid #334155;
      box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5);
      max-width: 600px;
      margin: 0 auto;
    }}
    h2 {{
      color: #38bdf8;
      margin-top: 0;
      font-size: 1.4rem;
      border-bottom: 1px solid #334155;
      padding-bottom: 12px;
    }}
    .badge {{
      display: inline-block;
      background: rgba(56, 189, 248, 0.15);
      color: #38bdf8;
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 600;
      margin-bottom: 16px;
    }}
    .loop-step {{
      display: flex;
      align-items: center;
      margin: 12px 0;
      padding: 12px;
      background: #0f172a;
      border-radius: 8px;
      border-left: 4px solid #38bdf8;
    }}
    .step-num {{
      font-size: 1.2rem;
      font-weight: 800;
      color: #38bdf8;
      width: 36px;
    }}
    .step-text {{
      font-size: 0.95rem;
      color: #e2e8f0;
    }}
    .source-tag {{
      margin-top: 20px;
      font-size: 0.8rem;
      color: #94a3b8;
      border-top: 1px dashed #334155;
      padding-top: 12px;
    }}
  </style>
</head>
<body>
  <div class="card">
    <span class="badge">Growth Framework Visualizer</span>
    <h2>Compounding Growth Loop Architecture</h2>
    <div class="loop-step">
      <div class="step-num">1</div>
      <div class="step-text"><strong>New User Sign-up:</strong> User activates through streamlined 3-milestone onboarding.</div>
    </div>
    <div class="loop-step">
      <div class="step-num">2</div>
      <div class="step-text"><strong>Core Value Created:</strong> User generates work product (project, board, document).</div>
    </div>
    <div class="loop-step">
      <div class="step-num">3</div>
      <div class="step-text"><strong>Teammate Collaboration:</strong> User shares or invites collaborators to participate.</div>
    </div>
    <div class="loop-step">
      <div class="step-num">4</div>
      <div class="step-text"><strong>Re-investment & Virality:</strong> Collaborators experience aha moment and become creators.</div>
    </div>
    <div class="source-tag">
      Evidence Grounding: <strong>{guest}</strong> ({title_src})
    </div>
  </div>
</body>
</html>"""
        content = sanitize_html_content(raw_html)
        content_format = "html"

    else:
        title = f"Growth Summary: {query.strip().title()[:60]}"
        content = f"# Growth Synthesis\n\nBased on evidence from **{guest}** in `{title_src}`."
        content_format = "markdown"

    word_count = len(content.split())
    reading_time = max(1, round(word_count / 200))

    return {
        "title": title,
        "content": content,
        "content_format": content_format,
        "schema_version": "v1.0",
        "artifact_metadata": {
            "word_count": word_count,
            "reading_time_minutes": reading_time,
            "primary_guest": guest,
            "primary_source_url": url_src,
            "primary_relative_path": rel_path,
            "citations": [c.model_dump() for c in citations],
            "supported_claims": [
                f"Activation milestone progression validated by {guest}",
                f"Compounding loops prioritized over linear funnels",
            ],
            "recommendations": [
                "Implement progressive profiling during signup",
                "Measure Day-30 retention curve flattening before paid ad scaling",
            ],
        },
    }
