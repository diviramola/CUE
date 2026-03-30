# Ads API Safety Rules (Meta + Google)

These rules apply to ALL code, scripts, agents, and automations that interact with Meta Marketing API or Google Ads API. They are non-negotiable and override any task-specific instructions.

## ABSOLUTE PROHIBITIONS
- NEVER use browser automation (Selenium, Puppeteer, Playwright) to interact with Meta Ads Manager or Google Ads UI. Use only official APIs.
- NEVER create, modify, pause, enable, archive, or delete campaigns/ad sets/ad groups/ads/creatives via API without explicit human approval in chat.
- NEVER change budgets, bids, spending limits, or bid strategies via API without explicit human approval in chat.
- NEVER auto-publish ad creatives through the API.
- NEVER exceed 50% of documented API rate limits.
- NEVER send purchase/conversion events via API without human review (triggers fraud detection).

## META MARKETING API LIMITS
- **Scoring**: Reads = 1 point, Writes = 3 points
- **Standard tier ceiling**: 9,000 points per 300-second window
- **Operating limit**: Stay at or below 4,500 points per 300-second window (50%)
- **Budget changes**: MAX 4 per hour per ad set (operate at MAX 2/hr)
- **Spending limit changes**: MAX 10 per day per account (operate at MAX 5/day)
- **Daily read call budget**: MAX 500 read calls per day for analytics/reporting
- **API version**: Pin explicitly (e.g., v23.0). Never use unversioned endpoints. Check quarterly for deprecations.
- **On HTTP 429 or error codes 17, 80001, 80002, 80003, 80004**: Exponential backoff starting at 60 seconds, max 4 retries.
- **On account restriction response**: STOP all API calls immediately. Alert human.

## GOOGLE ADS API LIMITS
- **Basic Access**: 15,000 operations/day
- **Test Access**: 15,000 operations/day (test accounts only)
- **Operating limit**: MAX 10,000 operations/day (67% of ceiling)
- **Daily call budget**: MAX 1,000 operations per day for analytics/reporting
- **Batch mutations**: Always batch multiple operations into single API requests
- **On RESOURCE_TEMPORARILY_EXHAUSTED**: Exponential backoff with jitter, starting at 5 seconds
- **Token keepalive**: Developer token must be used at least once every 90 days or it's auto-disabled. Schedule a monthly health-check ping.
- **RMF compliance**: If using Standard Access, meet all Required Minimum Functionality deadlines
- **Tool Change form**: Submit 2+ weeks before any material changes to the integration

## CIRCUIT BREAKER
- If >5 API errors occur within 60 seconds from either platform: PAUSE all API calls for 15 minutes
- If >20 errors in a single run: ABORT the run, alert human, do not retry automatically
- If any response indicates account restriction, policy violation, or suspicious activity flag: STOP immediately, do not retry

## OPERATIONAL SAFEGUARDS
- **Logging**: Every API call must be logged with: timestamp, endpoint, HTTP method, response code, points consumed (Meta)
- **New integrations**: Test on sandbox/test accounts for minimum 7 days before production
- **Warm-up**: New API connections should start with low-volume reads (10-20 calls) and scale gradually over 3-5 days
- **No bulk operations on day 1**: Never run full historical data pulls on the first day of a new API connection
- **Idempotency**: Add idempotency keys to all write operations to prevent duplicate actions
- **Version pinning**: Pin all API client library versions. No `latest` or `*` in dependencies.

## WHAT'S SAFE (autonomous, no approval needed)
- Pulling campaign performance data (impressions, clicks, spend, conversions)
- Reading ad creative metadata and thumbnails
- Fetching audience insights and demographics
- Downloading performance reports
- Reading account structure (campaigns, ad sets, ads hierarchy)
- Reading billing/spend summaries

## WHAT REQUIRES HUMAN APPROVAL (always ask first)
- Any write operation to ad platforms
- Any operation that changes campaign state (pause, enable, archive)
- Any budget or bid modification
- Creating new campaigns, ad sets, or ads
- Uploading creative assets
- Modifying audience targeting
- Changing conversion tracking settings

## MONITORING ALERTS
Generate an alert when:
- API usage exceeds 40% of any rate limit ceiling
- Any account restriction or policy violation response is received
- Google developer token approaches 60-day inactivity mark
- Meta API version is within 30 days of deprecation
- Error rate exceeds 10% in any 5-minute window
- Daily API call budget exceeds 80%
