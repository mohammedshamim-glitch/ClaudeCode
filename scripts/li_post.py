#!/usr/bin/env python3
import requests, os, json

token  = os.environ['LINKEDIN_TOKEN']
member = os.environ['LINKEDIN_MEMBER']
msg    = os.environ['MESSAGE']
tag    = os.environ['TAG']

r = requests.post(
    'https://api.linkedin.com/v2/ugcPosts',
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0',
    },
    json={
        'author': f'urn:li:person:{member}',
        'lifecycleState': 'PUBLISHED',
        'specificContent': {
            'com.linkedin.ugc.ShareContent': {
                'shareCommentary': {'text': msg},
                'shareMediaCategory': 'NONE',
            }
        },
        'visibility': {'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'},
    },
)

post_id = r.headers.get('x-restli-id', '')
out = {
    'status': r.status_code,
    'post_id': post_id,
    'post_url': f'https://www.linkedin.com/feed/update/{post_id}' if post_id else '',
    'body': r.text[:1000],
}

os.makedirs('linkedin_results', exist_ok=True)
with open(f'linkedin_results/{tag}.json', 'w') as f:
    json.dump(out, f, indent=2)

print(json.dumps(out, indent=2))
