# Parkwood Accord - Requirements Document

## Project Overview
iOS app for couples spending - helps partners track shared expenses, set budgets, and improve financial communication.

## Market Research

### Target Market Segments
1. **Couples Living Together** - Married, engaged, or long-term partners sharing finances
2. **Newlyweds** - Recently married couples establishing financial habits
3. **Roommates** - Non-romantic partners sharing housing expenses
4. **Financial Counselors** - Professionals recommending tools to clients

### Market Size & Trends
- US marriage rate: ~2M marriages/year
- ~60% of US adults live with a partner
- Couples finance apps market growing with increased focus on financial wellness
- Post-pandemic rise in joint financial management tools
- Increasing awareness of "financial infidelity" and need for transparency

### Competitive Landscape
- **Direct Competitors**:
  - Honeydue (specifically for couples)
  - Zeta (couples finance app)
  - Goodbudget (envelope budgeting, couples mode)
  - Splitwise (expense sharing, popular with roommates)
- **Indirect**:
  - Mint, YNAB (personal finance with sharing features)
  - Venmo/P2P apps (for settling up)
  - Excel/Google Sheets (manual tracking)

### Differentiation Opportunities
- Deeper focus on financial communication and goals, not just tracking
- Integration with couples' therapy/coaching workflows
- Unique features for specific couple dynamics (income disparity, different money personalities)
- Potential for async communication features around expenses
- Focus on iOS experience (Justin's expertise)

## Revenue Models

### 1. Subscription Model
- **Basic** (Free): Essential expense tracking, basic budgets
- **Premium** ($3.99-6.99/month): Advanced insights, goal setting, export, ad-free
- **Couples Therapy Bundle** ($9.99/month): Premium + communication exercises, shared journals

### 2. One-time Purchase
- $19.99 lifetime access (with free updates for 2 years)
- Optional annual support/update fee ($4.99/year)

### 3. B2B2C Model
- License to financial advisors, couples therapists
- White-label version for religious organizations (pre-marital counseling)
- Corporate wellness programs (employee relationship/financial wellness)

### 4. Affiliate/Referral
- Partner with recommended financial products (joint accounts, insurance)
- Referral fees from recommended couples retreats/counseling
- Amazon Associates for household products tracked in app

## Technical Requirements

### Core Features
- Shared expense tracking with categorization
- Split calculation (even, percentage, custom splits)
- Budget creation with rollover capabilities
- Goal setting (vacation, home purchase, emergency fund)
- Bill tracking and reminders
- Shared shopping lists
- Financial health dashboard (combined net worth, cash flow)
- Communication tools (comments on expenses, shared notes)
- Data export (CSV, PDF)
- Multi-currency support
- Receipt scanning/OCR integration

### Tech Stack
- Primary: Swift/SwiftUI (Justin's iOS expertise)
- Backend Options:
  - Firebase (easiest for auth, real-time sync)
  - Custom Node.js/Python API with PostgreSQL
  - Realm/SQLite with iCloud sync (for self-hosted preference)
- Authentication: Email/password, Apple Sign-in
- Deployment: App Store distribution
- Analytics: Firebase Analytics or Mixpanel

### Integration Points
- Apple Health (for health-related expense categorization)
- Apple Wallet (for transaction import)
- Banking APIs (via Plaid, later)
- Calendar integration (for recurring expenses/bills)
- Photos integration (for receipt capture)

## Go-to-Market Strategy

### Phase 1: Validation (Month 1)
- Build MVP with core expense splitting and tracking
- Target engaged couples through wedding forums, Facebook groups
- Offer free beta in exchange for feedback
- Interview 20+ couples about pain points

### Phase 2: Launch (Month 2-3)
- App Store launch with ASO optimization
- Content marketing: blog posts about money talks for couples
- Pinterest/wedding blog outreach
- Reddit engagement (r/personalfinance, r/relationships)
- Couples therapist outreach for reviews

### Phase 3: Growth (Month 4-6)
- Develop premium features based on user feedback
- Referral program (free month for both couples when referring)
- Wedding fair/expo appearances (virtual or physical)
- Partnership with engagement ring jewelers or wedding planners
- Localized versions for non-US markets (UK, CA, AU)

## Success Metrics
- **User Acquisition**: 500 active couples in first 3 months
- **Engagement**: 70% weekly active users, 3+ expenses logged/week/couple
- **Retention**: 40% month-over-month retention
- **Revenue**: $1,000 MRR by month 4, scaling to $5K by month 6
- **NPS**: >40 (positive word-of-mouth potential)
- **Churn**: <5% monthly for paid users

## Open Questions & Next Steps
1. What specific features does Justin envision beyond basic expense tracking?
2. Are there existing wireframes, designs, or user flows?
3. What level of bank integration is desired (manual vs. automated)?
4. Should we start with iOS-only or consider cross-platform later?
5. What privacy/security considerations are paramount for financial data?

## Research Sources to Consult
- Pew Research on couples and finances
- Gottman Institute research on money conflicts in relationships
- Wedding industry reports (The Knot, WeddingWire)
- Financial therapy literature
- App Store reviews of competing couples finance apps
- Google Trends for "couples budgeting", "money arguments relationship"