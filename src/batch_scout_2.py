"""Batch add round 2 - family/lower-middle-class focused ads."""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from harness import save_ad

ads = [
    {
        "id": "ad_011",
        "advertiser": "Meesho",
        "platform": "YouTube",
        "format": "TVC",
        "duration_seconds": 30,
        "language": "Hindi",
        "url": "https://www.adgully.com/aise-kaise-meesho-s-mega-sale-with-kapil-sharma-and-tamannaah-bhatia-150203.html",
        "source": "web_search",
        "date_found": "2026-03-28",
        "date_published": "2024-09",
        "vertical": "E-commerce/value",
        "region": "India",
        "tier": None,
        "tier_notes": "",
        "description": "Mega Blockbuster Sale campaign with Kapil Sharma and Tamannaah Bhatia. Five ads set against festive backdrops showing families discovering unbelievable deals. Tagline Aise Kaise captures the surprise of finding great prices on ethnic fashion, kidswear, home items. Targets Tier 2-3 families shopping on a budget.",
        "why_included": "Meesho is THE lower-middle-class brand in India. Their ads specifically target families of 4-5 in Tier 2-3 cities — exactly Wiom's audience. Celebrity plus value-messaging plus festive context is a proven formula for this segment. 100 percent Day 1 order increase proves it worked.",
        "tags": ["family", "value-messaging", "celebrity", "festive", "tier-2-3", "lower-middle-class", "budget-conscious"],
        "deconstructed": False
    },
    {
        "id": "ad_012",
        "advertiser": "Surf Excel",
        "platform": "YouTube",
        "format": "TVC",
        "duration_seconds": 45,
        "language": "Hindi",
        "url": "https://www.campaignindia.in/article/surf-excel-urges-consumers-to-celebrate-stains/410607",
        "source": "web_search",
        "date_found": "2026-03-28",
        "date_published": "2024-01",
        "vertical": "FMCG/household",
        "region": "India",
        "tier": None,
        "tier_notes": "",
        "description": "Daag Acche Hain evolution. Kids getting messy while doing something kind or brave, with parents initially worried about stains then realizing the stain tells a story of good values. Transforms a mundane product into an emotional story about parenting and childhood. Multi-generational Indian advertising icon.",
        "why_included": "The blueprint for family-targeted advertising in India. Shows kids plus parents in authentic middle-class homes. Turns a commodity product into an emotional choice. Wiom faces the same commodity challenge with broadband. If Surf Excel can make detergent emotional, Wiom can make internet emotional.",
        "tags": ["family", "kids", "emotional", "middle-class", "parenting", "commodity-to-emotion", "iconic"],
        "deconstructed": False
    },
    {
        "id": "ad_013",
        "advertiser": "Tata Tea",
        "platform": "YouTube",
        "format": "TVC",
        "duration_seconds": 60,
        "language": "Hindi",
        "url": "https://beastoftraal.com/2025/01/06/the-10-best-indian-ads-of-2024/",
        "source": "web_search",
        "date_found": "2026-03-28",
        "date_published": "2024-01",
        "vertical": "FMCG/beverage",
        "region": "India",
        "tier": None,
        "tier_notes": "",
        "description": "Jaago Re 2024 campaign addressing generational differences in how Indians perceive patriotism. Heartfelt conversations between parents and kids in a middle-class living room. The family debates what loving your country means today versus 30 years ago. Sparked widespread social media debate.",
        "why_included": "Middle-class living room as the stage. Parent-child generational tension as the hook. This is the exact household Wiom targets: family of 4-5 sitting together, different generations with different worldviews, united by shared moments at home. The debate format drives massive shareability.",
        "tags": ["family", "generational", "living-room", "debate", "shareability", "middle-class", "social-commentary"],
        "deconstructed": False
    }
]

for ad in ads:
    ok, msg = save_ad(ad)
    print(f"{'OK' if ok else 'FAIL'} | {msg}")
