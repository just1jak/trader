# CampingSniper - Requirements Document

## Project Overview
Campsite availability monitor hitting Recreation.gov's internal API. Sends Slack alerts.

## Market Research

### Target Market Segments
1. **Avid Campers** - People who frequently camp at popular national parks and federal recreation sites
2. **Last-Minute Planners** - Campers who often decide to go camping with short notice
3. **RV Owners** - Those needing specific site types (full hookup, pull-through, etc.)
4. **Group Camp Leaders** - People organizing camping trips for families, clubs, or organizations
5. **Outdoor Recreation Businesses** - Guides, outfitters needing reliable campsite access for clients

### Market Size & Trends
- Recreation.gov manages ~100,000+ campsites across federal lands
- US camping participation: ~50M households camp annually (2022 data)
- National Park Service visits: ~300M+ annually
- Increasing difficulty securing campsites at popular destinations
- Growth in "hipcamp" and private camping alternatives shows demand
- Social media influence driving interest in specific, photogenic campsites
- Rise of dispersed camping and BLM land use as alternatives

### Competitive Landscape
- **Direct Competitors**:
  - Campnab (campsite availability monitoring)
  - The Dyrt (campground info + availability)
  - Hipcamp (private land camping, some availability features)
  - ReserveAmerica/Recreation.gov's own notification system (limited)
- **Indirect**:
  - Recreation.gov website (manual checking)
  - Various Facebook groups sharing cancellation tips
  - Spreadsheet-based tracking methods
  - Ranger stations/phone calls (traditional method)

### Differentiation Opportunities
- Focus on Recreation.gov's internal API (potentially faster/more reliable than public site)
- Slack-based alerts (meets users where they already communicate)
- Customizable filtering (site type, amenities, dates, length of stay)
- Group coordination features (multiple users tracking same dates)
- Historical availability data for planning future trips
- Integration with calendar apps for automatic trip planning
- Potential expansion to other reservation systems (state parks, etc.)

## Revenue Models

### 1. Subscription Model
- **Free Tier**: Basic monitoring for 1-2 campgrounds, daily checks
- **Pro Tier** ($2.99-4.99/month): Unlimited campgrounds, hourly checks, SMS alerts
- **Premium Tier** ($7.99-9.99/month): All features + historical data, group planning, export
- **Team/Group** ($12.99/month): Multiple users, shared lists, admin controls

### 2. One-time Purchase
- $19.99 lifetime license (with check frequency limitations)
- Optional annual renewal for updated API access ($4.99/year)

### 3. Affiliate/Partnership
- Referral fees from recommended camping gear (when users book trips)
- Partnerships with outdoor retailers (REI, Bass Pro Shops)
- Affiliate links to recommended campsites via Hipcamp or similar
- Sponsored content from camping-related brands

### 4. Data/Services
- Sell aggregated campsite availability trends to campground managers
- Custom monitoring services for outfitters/guides
- API access for developers building camping-related tools
- Consultation for optimizing camping trip planning

### 5. Merchandise
- Branded camping gear (stickers, patches for successful bookings)
- Digital camping planners/checklists
- Printable trip logs and journals

## Technical Requirements

### Core Features
- Monitor Recreation.gov API for campsite availability
- Customizable search parameters (campground, dates, site type, equipment)
- Flexible alert thresholds (immediate notification, daily summary)
- Multiple notification channels (Slack, SMS, email, push notifications)
- Historical availability tracking and trends
- Calendar integration (iCal, Google Camping)
- Trip planning assistance (suggest alternatives, optimal dates)
- User profiles and preference saving
- Multi-user/group coordination features
- Mobile-responsive web interface
- Rate limiting and respectful API usage

### Tech Stack
- Backend: Python/FastAPI or Node.js (aligns with existing n8n skills)
- Database: PostgreSQL or Redis for caching/API responses
- Frontend: React/Vue.js for dashboard or simple HTML/CSS
- Deployment: Docker container (fits Proxmox homelab)
- Authentication: Email/password, magic links, or OAuth
- API Integration: Recreation.gov internal API (needs investigation)
- Notifications: Slack webhooks, Twilio (SMS), SMTP (email), APNS/FCM (push)
- Hosting: VPS or homelab with reverse proxy (NGINX)

### Integration Points
- Recreation.gov API (primary data source)
- Slack (primary notification channel per description)
- Google Calendar/Apple Calendar (trip planning)
- Weather APIs (for trip planning enhancement)
- Maps APIs (for campsite location visualization)
- Potential future: State park systems, Hipcamp, ReserveAmerica

## Go-to-Market Strategy

### Phase 1: Validation (Month 1)
- Build MVP monitoring 1-2 popular campgrounds
- Test with personal use and close friends/family
- Engage with camping subreddits (r/camping, r/RVing)
- Offer free beta in exchange for feedback on accuracy/speed
- Document API endpoints and rate limits

### Phase 2: Launch (Month 2-3)
- ProductHunt launch (targeting productivity/tools category)
- Reddit marketing in relevant communities (with value-first approach)
- Instagram/Pinterest targeting camping aesthetics
- Outreach to camping blogs and YouTube channels
- Early bird pricing for first 100 subscribers
- Develop detailed documentation and use cases

### Phase 3: Growth (Month 4-6)
- Add more campgrounds based on user requests
- Develop premium features (historical data, group planning)
- Partnership with camping gear retailers for bundles
- Create content marketing (blog posts about camping planning)
- Develop mobile app version (React Native or native)
- Expand to state park systems if Recreation.gov API proves model

### Phase 4: Expansion (Month 6-12)
- International expansion (Canada's reservation system, etc.)
- White-label for outfitters/guide services
- API licensing for other developers
- Consider acquisition by larger camping/recreation companies
- Explore hardware integration (smart camping gear alerts)

## Success Metrics
- **User Acquisition**: 200 active users in first 3 months
- **Engagement**: 50% weekly active users, avg 3+ active monitors/user
- **Accuracy**: >95% alert accuracy vs. manual checks
- **Response Time**: Alerts within 15 minutes of availability (goal)
- **Revenue**: $500 MRR by month 3, scaling to $2K by month 6
- **Retention**: 60% month-over-month for paid users
- **NPS**: >30 (indicating strong word-of-mouth potential)
- **Alert-to-Booking**: Track percentage of alerts that lead to confirmed bookings

## Open Questions & Next Steps
1. What specific Recreation.gov internal API endpoints are being used?
2. What is the current check frequency and latency?
3. Which campgrounds are currently being monitored?
4. What Slack integration details exist (webhook, bot token, etc.)?
5. Are there existing users beyond Justin providing feedback?
6. What programming language/framework is the current version built in?

## Research Sources to Consult
- Recreation.gov API documentation (if available publicly)
- FOIA requests for API details (if needed)
- National Park Service statistics and visitation data
- Google Trends for camping-related searches
- Analysis of successful campsite monitoring tools
- Legal/terms of service considerations for API usage
- User surveys about camping planning pain points