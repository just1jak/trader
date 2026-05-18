# Smart Money Tracker - Requirements Document

## Project Overview
Financial risk scoring system (currently V5.1) designed to help individuals and businesses assess financial risk exposure.

## Market Research

### Target Market Segments
1. **Individual Investors** - Retail investors seeking to understand portfolio risk
2. **Small Business Owners** - SMBs needing basic financial health monitoring
3. **Financial Advisors** - Professionals wanting risk assessment tools for clients
4. **Fintech Companies** - Companies needing risk scoring APIs for their platforms

### Market Size & Trends
- Global fintech market projected to reach $698.48B by 2030 (CAGR 20.5%)
- Risk management software market expected to grow to $21.5B by 2027
- Increasing demand for personal finance tools post-pandemic
- Regulatory pressure driving need for better risk assessment

### Competitive Landscape
- **Direct Competitors**: 
  - Credit Karma (personal finance focus)
  - Mint (budgeting with some risk elements)
  - Personal Capital (wealth management)
- **Indirect/Enterprise**:
  - Moody's Analytics
  - RiskMetrics (MSCI)
  - Bloomberg Risk Management
  - SAS Risk Management

### Differentiation Opportunities
- Self-hosted solution appealing to privacy-conscious users
- Integration with existing homelab stack (Nextcloud, Actual Budget)
- Focus on actionable insights vs. just scores
- Potential for custom risk models based on user-specific data

## Revenue Models

### 1. Freemium SaaS Model
- **Free Tier**: Basic risk scoring, limited historical data
- **Pro Tier** ($5-15/month): Advanced models, scenario planning, export capabilities
- **Business Tier** ($25-50/month/user): Team features, API access, custom models

### 2. License/Model
- One-time purchase for self-hosted version ($49-99)
- Annual updates/support subscription ($19/year)

### 3. Data/API Monetization
- Aggregated, anonymized market risk insights (B2B)
- Custom risk model development for enterprises
- White-label solutions for financial advisors

### 4. Affiliate/Partnership
- Referral fees from recommended financial products
- Partnerships with accounting software (QuickBooks, Xero)
- Integration with investment platforms

## Technical Requirements

### Core Features
- Multi-factor risk assessment (debt, income volatility, investment exposure, liquidity)
- Scenario modeling (job loss, market downturn, expense shocks)
- Trend analysis and risk progression tracking
- Integration with financial data sources (Plaid, manual CSV import, Actual Budget)
- Alert system for risk threshold breaches
- Exportable reports (PDF, CSV)

### Tech Stack Preferences
- Backend: Python/FastAPI or Node.js (aligns with existing n8n skills)
- Database: PostgreSQL or SQLite (for self-hosted simplicity)
- Frontend: React/Vue.js or simple dashboard (initially)
- Deployment: Docker container (fits Proxmox homelab)
- Authentication: Basic auth or OAuth2 (future)

### Integration Points
- Actual Budget (for expense/income data)
- Nextcloud (file storage for reports/backups)
- n8n (workflow automation for data collection)
- Potential Plaid/Open Banking integration (later)

## Go-to-Market Strategy

### Phase 1: Validation (Month 1-2)
- Build MVP with core scoring algorithm
- Target homelab/self-hosting communities (r/selfhosted, r/homelab)
- Offer free version for feedback
- Collect use cases and pain points

### Phase 2: Early Adopters (Month 3-4)
- Launch paid tiers
- Target personal finance blogs/newsletters for reviews
- Partner with financial independence communities (FIRE movement)
- Create educational content about financial risk

### Phase 3: Growth (Month 5-6)
- Develop API for B2B licensing
- Target financial advisors and coaches
- Explore white-label opportunities
- Consider mobile companion app

## Success Metrics
- **User Acquisition**: 100 active users in first 3 months
- **Conversion**: 5-10% free to paid conversion
- **Revenue**: $500 MRR by month 6
- **Engagement**: Weekly active users >60% of total
- **Retention**: Monthly churn <5%

## Open Questions & Next Steps
1. What specific risk factors does current V5.1 model assess?
2. What data sources are currently integrated?
3. What programming language/framework is V5.1 built in?
4. Are there existing users or testers for feedback?
5. What makes this risk scoring unique compared to basic debt-to-income ratios?

## Research Sources to Consult
- FDIC consumer finance surveys
- Federal Reserve household debt reports
- Fintech adoption statistics (Statista, McKinsey)
- Open banking/API trends
- Personal finance app reviews and pain points