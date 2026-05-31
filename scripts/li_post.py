#!/usr/bin/env python3
import requests, os, json

token   = os.environ['LINKEDIN_TOKEN']
member  = os.environ['LINKEDIN_MEMBER']
msg     = os.environ['MESSAGE']
tag     = os.environ['TAG']
img_url = os.environ.get('IMAGE_URL', '').strip()

HEADERS = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'X-Restli-Protocol-Version': '2.0.0',
}


def upload_image(url):
    # Step 1: register upload
    reg = requests.post(
        'https://api.linkedin.com/v2/assets?action=registerUpload',
        headers=HEADERS,
        json={
            'registerUploadRequest': {
                'recipes': ['urn:li:digitalmediaRecipe:feedshare-image'],
                'owner': f'urn:li:person:{member}',
                'serviceRelationships': [{
                    'relationshipType': 'OWNER',
                    'identifier': 'urn:li:userGeneratedContent',
                }],
            }
        },
    )
    if not reg.ok:
        print(f'Image register failed: {reg.status_code} {reg.text}')
        return None

    data        = reg.json()
    asset_urn   = data['value']['asset']
    upload_url  = data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']

    # Step 2: upload binary
    img_data = requests.get(url, timeout=30).content
    up = requests.put(upload_url, data=img_data,
                      headers={'Authorization': f'Bearer {token}',
                               'Content-Type': 'image/jpeg'})
    if up.status_code not in (200, 201):
        print(f'Image upload failed: {up.status_code}')
        return None

    print(f'Image uploaded: {asset_urn}')
    return asset_urn


asset_urn = upload_image(img_url) if img_url else None

if asset_urn:
    share_content = {
        'shareCommentary': {'text': msg},
        'shareMediaCategory': 'IMAGE',
        'media': [{
            'status': 'READY',
            'description': {'text': ''},
            'media': asset_urn,
            'title': {'text': ''},
        }],
    }
else:
    share_content = {
        'shareCommentary': {'text': msg},
        'shareMediaCategory': 'NONE',
    }

r = requests.post(
    'https://api.linkedin.com/v2/ugcPosts',
    headers=HEADERS,
    json={
        'author': f'urn:li:person:{member}',
        'lifecycleState': 'PUBLISHED',
        'specificContent': {'com.linkedin.ugc.ShareContent': share_content},
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
