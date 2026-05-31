#!/usr/bin/env python3
"""
Digital Fusion — LinkedIn Post via Zapier Webhook
Usage: python3 digital_fusion_linkedin.py <post_file>
       python3 digital_fusion_linkedin.py --text "Your post text here"
"""

import sys, json, requests

ZAPIER_WEBHOOK = "https://hooks.zapier.com/hooks/catch/27389018/4bhsov8/"


def post_to_linkedin(message):
    r = requests.post(ZAPIER_WEBHOOK, json={"message": message})
    if r.status_code in (200, 201):
        print("✓ Posted to LinkedIn via Zapier")
    else:
        print(f"ERROR {r.status_code}: {r.text}")


POSTS = {
    "ai_gap": """There's a growing gap between the AI being deployed by governments and militaries — and what the rest of us can access.

It's bigger than most people realise, and it's accelerating fast.

We break it down in our latest Digital Fusion video 👇

🎥 The Military-Grade AI Gap: What Governments Aren't Telling You
https://www.youtube.com/watch?v=suv3m6nQkbk

#AI #ArtificialIntelligence #MilitaryTech #TechNews #DigitalFusion""",

    "nft_bubble": """NFTs were selling for millions. Then almost overnight — they weren't.

What actually happened? And what does it tell us about the next digital asset bubble?

🎥 The NFT Bubble: How Digital Art Went From Millions to Worthless
https://www.youtube.com/watch?v=cH6zmhWf_iU

#NFT #Crypto #Blockchain #DigitalAssets #TechNews #DigitalFusion"""
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 digital_fusion_linkedin.py [ai_gap|nft_bubble]")
        print("       python3 digital_fusion_linkedin.py --text 'Your message'")
        sys.exit(1)

    if sys.argv[1] == "--text":
        message = sys.argv[2]
    elif sys.argv[1] in POSTS:
        message = POSTS[sys.argv[1]]
    else:
        print(f"Unknown post key: {sys.argv[1]}")
        sys.exit(1)

    post_to_linkedin(message)


if __name__ == "__main__":
    main()
