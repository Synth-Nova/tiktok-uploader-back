#!/usr/bin/env python3
"""
Use playwright to capture network requests from GeeLark API docs page
"""
import asyncio
import json

async def main():
    from playwright.async_api import async_playwright
    
    api_requests = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Capture all network requests
        async def handle_request(request):
            url = request.url
            if 'geelark' in url and not url.endswith(('.js', '.css', '.png', '.svg', '.ico', '.woff', '.woff2')):
                api_requests.append({
                    'method': request.method,
                    'url': url,
                    'headers': dict(request.headers) if request.headers else {}
                })
        
        async def handle_response(response):
            url = response.url
            if 'geelark' in url and '/api' in url.lower():
                try:
                    body = await response.text()
                    print(f"\n📥 Response from {url}")
                    print(f"   Status: {response.status}")
                    print(f"   Body preview: {body[:500]}...")
                except:
                    pass
        
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        print("Loading https://open.geelark.com/api ...")
        await page.goto('https://open.geelark.com/api', wait_until='networkidle', timeout=60000)
        
        # Wait for page to fully load
        await asyncio.sleep(5)
        
        # Get page content
        content = await page.content()
        print(f"\nPage loaded, content length: {len(content)}")
        
        # Try to extract text content
        text = await page.inner_text('body')
        print(f"\nPage text (first 3000 chars):\n{text[:3000]}")
        
        # Print all captured requests
        print(f"\n\n{'='*60}")
        print(f"Captured {len(api_requests)} API-related requests:")
        print('='*60)
        for req in api_requests:
            print(f"\n{req['method']} {req['url']}")
        
        await browser.close()

asyncio.run(main())
