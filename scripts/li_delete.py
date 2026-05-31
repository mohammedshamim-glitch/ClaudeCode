#!/usr/bin/env python3
import requests, os, json, urllib.parse

token = os.environ['LINKEDIN_TOKEN']
urn   = os.environ['URN']  # e.g. urn:li:share:7466767705107308544

encoded = urllib.parse.quote(urn, safe='')
results = {}

# Try ugcPosts delete
r1 = requests.delete(
    f'https://api.linkedin.com/v2/ugcPosts/{encoded}',
    headers={'Authorization': f'Bearer {token}', 'X-Restli-Protocol-Version': '2.0.0'},
)
results['ugcPosts'] = {'status': r1.status_code, 'body': r1.text[:300]}

# Try shares delete (numeric id) if ugcPosts didn't work
if r1.status_code not in (200, 204):
    share_id = urn.split(':')[-1]
    r2 = requests.delete(
        f'https://api.linkedin.com/v2/shares/{share_id}',
        headers={'Authorization': f'Bearer {token}', 'X-Restli-Protocol-Version': '2.0.0'},
    )
    results['shares'] = {'status': r2.status_code, 'body': r2.text[:300]}

os.makedirs('linkedin_results', exist_ok=True)
with open('linkedin_results/delete_result.json', 'w') as f:
    json.dump(results, f, indent=2)
print(json.dumps(results, indent=2))
