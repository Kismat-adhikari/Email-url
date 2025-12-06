# Email Enrichment System

Advanced email enrichment with domain metadata, geolocation inference, and engagement scoring.

## Features

### Domain Classification
- ✅ **Provider Type** - Corporate, Free, Educational, Government
- ✅ **Domain Metadata** - Detailed classification flags
- ✅ **Industry Detection** - 12+ industry categories
- ✅ **Company Size** - Enterprise, Mid-market, Small, Individual

### Geolocation
- ✅ **Country Detection** - From TLD (40+ countries)
- ✅ **Region Mapping** - Europe, Asia, Americas, etc.
- ✅ **Confidence Levels** - High, Medium, Low, None
- ✅ **Generic TLD Handling** - .com, .net, .org, .edu, .gov

### Engagement Scoring
- ✅ **0-100 Score** - Based on multiple factors
- ✅ **Validation Integration** - Uses validation data
- ✅ **Domain Quality** - Corporate > Free
- ✅ **Bounce History** - Penalizes bounces
- ✅ **Segmentation Ready** - For marketing campaigns

## Installation

```bash
# No additional dependencies required
# Uses standard Python libraries
```

## Quick Start

### Basic Enrichment

```python
from email_enrichment import enrich_email

result = enrich_email('john@acme-corp.co.uk')

print(f"Domain Type: {result['domain_type']}")
print(f"Country: {result['geolocation']['country']}")
print(f"Engagement Score: {result['engagement_score']}")
print(f"Industry: {result['industry']}")
```

**Output:**
```
Domain Type: corporate
Country: United Kingdom
Engagement Score: 50
Industry: None
```

### With Validation Data

```python
from email_enrichment import EmailEnrichment

enricher = EmailEnrichment()

validation_data = {
    'valid': True,
    'confidence_score': 95,
    'bounce_count': 0,
    'is_disposable': False,
    'is_role_based': False
}

result = enricher.enrich_email('john@techcorp.com', validation_data)

print(f"Engagement Score: {result['engagement_score']}")  # High score!
```

## Domain Type Classification

### Free Providers

Detected free email providers:
- Gmail, Yahoo, Hotmail, Outlook
- iCloud, AOL, ProtonMail
- Zoho, GMX, Yandex
- 20+ providers total

```python
result = enrich_email('user@gmail.com')
print(result['domain_type'])  # 'free'
print(result['provider_type'])  # 'consumer'
print(result['is_free_provider'])  # True
```

### Corporate Domains

Non-free, non-educational, non-government domains:

```python
result = enrich_email('john@acme-corp.com')
print(result['domain_type'])  # 'corporate'
print(result['provider_type'])  # 'business'
print(result['is_corporate'])  # True
```

### Educational Domains

.edu domains or containing education keywords:

```python
result = enrich_email('student@university.edu')
print(result['domain_type'])  # 'educational'
print(result['provider_type'])  # 'education'
```

### Government Domains

.gov domains or containing government keywords:

```python
result = enrich_email('official@agency.gov')
print(result['domain_type'])  # 'government'
print(result['provider_type'])  # 'government'
```

## Geolocation Inference

### Country-Specific TLDs

Supports 40+ country TLDs:

```python
enricher = EmailEnrichment()

# United Kingdom
geo = enricher.infer_geolocation('example.co.uk')
print(geo['country'])  # 'United Kingdom'
print(geo['country_code'])  # 'UK'
print(geo['region'])  # 'Europe'
print(geo['confidence'])  # 'high'

# Germany
geo = enricher.infer_geolocation('example.de')
print(geo['country'])  # 'Germany'

# Japan
geo = enricher.infer_geolocation('example.jp')
print(geo['country'])  # 'Japan'
print(geo['region'])  # 'Asia'
```

### Supported Countries

**Europe:** UK, DE, FR, IT, ES, NL, BE, CH, AT, SE, NO, DK, FI, PL, CZ, IE, PT, GR

**Asia:** JP, CN, IN, KR, TW, TH, MY, ID, PH, VN, SG, HK

**Americas:** US, CA, BR, MX, AR, CL, CO

**Oceania:** AU, NZ

**Middle East:** AE, SA, IL, TR

**Africa:** ZA, EG

### Generic TLDs

```python
geo = enricher.infer_geolocation('example.com')
print(geo['region'])  # 'Global/United States'
print(geo['confidence'])  # 'low'

geo = enricher.infer_geolocation('university.edu')
print(geo['region'])  # 'United States (Education)'
```

## Engagement Scoring

### Scoring Factors (0-100 points)

| Factor | Points | Description |
|--------|--------|-------------|
| Email Valid | 30 | Email passes validation |
| Domain Type | 20 | Corporate=20, Educational=15, Free=10 |
| Confidence Score | 20 | Scaled from validation confidence |
| No Bounces | 15 | 0 bounces=15, 1=10, 2=5, 3+=0 |
| Not Disposable | 10 | Not a temporary email |
| Not Role-based | 5 | Not generic (info, admin) |
| **Total** | **100** | Maximum score |

### Score Interpretation

| Score | Level | Meaning |
|-------|-------|---------|
| 90-100 | Excellent | High-value contact |
| 70-89 | Good | Quality contact |
| 50-69 | Fair | Average contact |
| 30-49 | Poor | Low engagement potential |
| 0-29 | Very Poor | Avoid or re-verify |

### Examples

**Perfect Score (100):**
```python
result = enricher.calculate_engagement_score(
    'john@company.com',
    {'is_corporate': True},
    {
        'valid': True,
        'confidence_score': 100,
        'bounce_count': 0,
        'is_disposable': False,
        'is_role_based': False
    }
)
print(result)  # 100
```

**Low Score:**
```python
result = enricher.calculate_engagement_score(
    'test@tempmail.com',
    {'is_free': True},
    {
        'valid': False,
        'confidence_score': 20,
        'bounce_count': 5,
        'is_disposable': True,
        'is_role_based': True
    }
)
print(result)  # ~14
```

## Industry Detection

Detects 12+ industries from domain keywords:

```python
enricher = EmailEnrichment()

print(enricher.detect_industry('techcorp.com'))  # 'Technology'
print(enricher.detect_industry('bankofamerica.com'))  # 'Finance'
print(enricher.detect_industry('healthclinic.com'))  # 'Healthcare'
print(enricher.detect_industry('university.edu'))  # 'Education'
print(enricher.detect_industry('consulting-group.com'))  # 'Consulting'
```

### Supported Industries

- Technology
- Finance
- Healthcare
- Education
- Retail
- Manufacturing
- Consulting
- Real Estate
- Legal
- Marketing
- Government
- Non-Profit

## Company Size Estimation

Estimates company size from domain characteristics:

```python
enricher = EmailEnrichment()

# Individual (free provider)
size = enricher.estimate_company_size(
    'gmail.com',
    {'is_free': True}
)
print(size)  # 'individual'

# Enterprise
size = enricher.estimate_company_size(
    'global-corp.com',
    {'is_corporate': True}
)
print(size)  # 'enterprise'

# Mid-market
size = enricher.estimate_company_size(
    'consulting-solutions.com',
    {'is_corporate': True}
)
print(size)  # 'mid-market'
```

### Size Categories

- **enterprise** - Global, international, worldwide
- **mid-market** - Solutions, services, consulting
- **small** - Local, shop, studio
- **individual** - Free email providers
- **large-organization** - Educational, government
- **small-to-mid** - Default corporate
- **unknown** - Cannot determine

## Complete Enrichment

### Full Result Structure

```python
result = enricher.enrich_email('john@acme-corp.co.uk', validation_data)
```

**Returns:**
```json
{
  "email": "john@acme-corp.co.uk",
  "domain": "acme-corp.co.uk",
  "local_part": "john",
  "domain_type": "corporate",
  "provider_type": "business",
  "is_free_provider": false,
  "is_corporate": true,
  "is_educational": false,
  "is_government": false,
  "geolocation": {
    "country": "United Kingdom",
    "country_code": "UK",
    "region": "Europe",
    "confidence": "high"
  },
  "engagement_score": 95,
  "industry": null,
  "company_size": "small-to-mid",
  "enriched_at": "2024-01-01T12:00:00"
}
```

## Batch Enrichment

```python
enricher = EmailEnrichment()

emails = [
    'john@company.com',
    'jane@gmail.com',
    'bob@university.edu'
]

results = enricher.batch_enrich(emails)

for result in results:
    print(f"{result['email']}: {result['domain_type']} - Score: {result['engagement_score']}")
```

**Output:**
```
john@company.com: corporate - Score: 50
jane@gmail.com: free - Score: 40
bob@university.edu: educational - Score: 45
```

## Integration Examples

### With Validation System

```python
from email_validator_smtp import validate_email_with_smtp
from email_enrichment import enrich_email

# Validate
validation = validate_email_with_smtp('john@company.com')

# Enrich with validation data
enrichment = enrich_email('john@company.com', validation)

print(f"Valid: {validation['valid']}")
print(f"Confidence: {validation['confidence_score']}")
print(f"Engagement Score: {enrichment['engagement_score']}")
print(f"Country: {enrichment['geolocation']['country']}")
```

### With Supabase Storage

```python
from supabase_storage import get_storage
from email_enrichment import enrich_email

storage = get_storage()

# Get validation record
record = storage.get_record_by_email('john@company.com')

# Enrich
enrichment = enrich_email('john@company.com', record)

# Update record with enrichment
storage.update_record(record['id'], {
    'notes': f"Industry: {enrichment['industry']}, Score: {enrichment['engagement_score']}"
})
```

### Segmentation for Marketing

```python
from email_enrichment import EmailEnrichment

enricher = EmailEnrichment()

def segment_email(email, validation_data):
    """Segment email for marketing campaigns."""
    enrichment = enricher.enrich_email(email, validation_data)
    
    score = enrichment['engagement_score']
    domain_type = enrichment['domain_type']
    
    if score >= 80 and domain_type == 'corporate':
        return 'high-value-b2b'
    elif score >= 70:
        return 'quality-leads'
    elif score >= 50:
        return 'nurture-campaign'
    else:
        return 'low-priority'

# Use in campaign
segment = segment_email('john@company.com', validation_data)
print(f"Segment: {segment}")
```

## Testing

### Run Unit Tests

```bash
python test_enrichment.py
```

### Test Coverage

- ✅ Domain type detection (free, corporate, educational, government)
- ✅ Geolocation inference (40+ countries)
- ✅ Engagement score calculation
- ✅ Industry detection (12+ industries)
- ✅ Company size estimation
- ✅ Batch enrichment
- ✅ Integration with validation data

**Result:** 32/32 tests passed ✅

## Use Cases

### 1. Lead Scoring

```python
# Score leads based on email quality
enrichment = enrich_email(lead_email, validation_data)

if enrichment['engagement_score'] >= 80:
    assign_to_sales_team(lead_email)
elif enrichment['engagement_score'] >= 50:
    add_to_nurture_campaign(lead_email)
else:
    mark_as_low_priority(lead_email)
```

### 2. Geographic Targeting

```python
# Target by region
enrichment = enrich_email(user_email)
region = enrichment['geolocation']['region']

if region == 'Europe':
    send_gdpr_compliant_email(user_email)
elif region == 'Americas':
    send_can_spam_compliant_email(user_email)
```

### 3. B2B vs B2C Segmentation

```python
# Segment by domain type
enrichment = enrich_email(contact_email)

if enrichment['is_corporate']:
    add_to_b2b_list(contact_email)
elif enrichment['is_free_provider']:
    add_to_b2c_list(contact_email)
```

### 4. Industry-Specific Campaigns

```python
# Target by industry
enrichment = enrich_email(prospect_email)

if enrichment['industry'] == 'Healthcare':
    send_healthcare_campaign(prospect_email)
elif enrichment['industry'] == 'Finance':
    send_finance_campaign(prospect_email)
```

## Best Practices

### 1. Always Validate First

```python
# Validate before enriching
validation = validate_email_with_smtp(email)

if validation['valid']:
    enrichment = enrich_email(email, validation)
    # Use enrichment data
```

### 2. Cache Enrichment Results

```python
# Cache to avoid repeated enrichment
cache = {}

def get_enrichment(email, validation_data):
    if email not in cache:
        cache[email] = enrich_email(email, validation_data)
    return cache[email]
```

### 3. Combine Multiple Signals

```python
# Use enrichment + validation + risk for complete picture
validation = validate_email_with_smtp(email)
enrichment = enrich_email(email, validation)
risk = assess_email_risk(email)

decision_score = (
    enrichment['engagement_score'] * 0.4 +
    validation['confidence_score'] * 0.3 +
    (100 - risk['risk_score']) * 0.3
)
```

## Limitations

- **Geolocation:** Based on TLD only, not IP-based
- **Industry:** Keyword-based, may not be 100% accurate
- **Company Size:** Estimated from domain characteristics
- **Free Providers:** List may not be exhaustive
- **Engagement Score:** Requires validation data for accuracy

## License

MIT License - Free to use in your projects

## Next Steps

1. ✅ Run tests: `python test_enrichment.py`
2. ✅ Try enrichment: `python -c "from email_enrichment import enrich_email; print(enrich_email('user@example.com'))"`
3. ✅ Integrate with validation system
4. ✅ Use for lead scoring
5. ✅ Implement segmentation

You're ready to enrich! 🚀
