"""
Browser Fingerprint Generator
Generates unique fingerprints matching specific countries
"""

import random
import hashlib
import json
from typing import Dict, List


# Country-specific configurations
COUNTRY_CONFIGS = {
    'us': {
        'name': 'United States',
        'language': 'en-US',
        'languages': ['en-US', 'en'],
        'timezone': 'America/New_York',
        'timezone_offset': -300,  # UTC-5
        'locales': ['en-US'],
    },
    'gb': {
        'name': 'United Kingdom', 
        'language': 'en-GB',
        'languages': ['en-GB', 'en'],
        'timezone': 'Europe/London',
        'timezone_offset': 0,  # UTC+0
        'locales': ['en-GB'],
    },
    'de': {
        'name': 'Germany',
        'language': 'de-DE',
        'languages': ['de-DE', 'de', 'en-US', 'en'],
        'timezone': 'Europe/Berlin',
        'timezone_offset': -60,  # UTC+1
        'locales': ['de-DE'],
    },
    'fr': {
        'name': 'France',
        'language': 'fr-FR',
        'languages': ['fr-FR', 'fr', 'en-US', 'en'],
        'timezone': 'Europe/Paris',
        'timezone_offset': -60,
        'locales': ['fr-FR'],
    },
    'es': {
        'name': 'Spain',
        'language': 'es-ES',
        'languages': ['es-ES', 'es', 'en'],
        'timezone': 'Europe/Madrid',
        'timezone_offset': -60,
        'locales': ['es-ES'],
    },
    'it': {
        'name': 'Italy',
        'language': 'it-IT',
        'languages': ['it-IT', 'it', 'en'],
        'timezone': 'Europe/Rome',
        'timezone_offset': -60,
        'locales': ['it-IT'],
    },
    'br': {
        'name': 'Brazil',
        'language': 'pt-BR',
        'languages': ['pt-BR', 'pt', 'en'],
        'timezone': 'America/Sao_Paulo',
        'timezone_offset': 180,  # UTC-3
        'locales': ['pt-BR'],
    },
    'mx': {
        'name': 'Mexico',
        'language': 'es-MX',
        'languages': ['es-MX', 'es', 'en'],
        'timezone': 'America/Mexico_City',
        'timezone_offset': 360,  # UTC-6
        'locales': ['es-MX'],
    },
}

# Realistic User Agents (Chrome on Windows/Mac)
USER_AGENTS = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Mac Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Screen resolutions (common desktop)
SCREEN_RESOLUTIONS = [
    (1920, 1080),
    (1366, 768),
    (1536, 864),
    (1440, 900),
    (1280, 720),
    (2560, 1440),
    (1600, 900),
    (1280, 800),
]

# WebGL Renderers (realistic GPU names)
WEBGL_RENDERERS = [
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Apple Inc.", "Apple M1"),
    ("Apple Inc.", "Apple M2"),
]

# Common fonts per platform
WINDOWS_FONTS = [
    "Arial", "Arial Black", "Calibri", "Cambria", "Cambria Math",
    "Comic Sans MS", "Consolas", "Courier New", "Georgia", "Impact",
    "Lucida Console", "Lucida Sans Unicode", "Microsoft Sans Serif",
    "Palatino Linotype", "Segoe UI", "Tahoma", "Times New Roman",
    "Trebuchet MS", "Verdana", "Wingdings"
]

MAC_FONTS = [
    "Arial", "Arial Black", "Comic Sans MS", "Courier New", "Georgia",
    "Helvetica", "Helvetica Neue", "Impact", "Lucida Grande", "Monaco",
    "Palatino", "Times", "Times New Roman", "Trebuchet MS", "Verdana",
    "San Francisco", "SF Pro Display", "SF Pro Text"
]


def generate_canvas_noise_seed() -> int:
    """Generate unique canvas noise seed"""
    return random.randint(100000, 999999)


def generate_audio_hash() -> str:
    """Generate unique audio context hash"""
    data = str(random.random()) + str(random.randint(0, 1000000))
    return hashlib.md5(data.encode()).hexdigest()[:16]


def generate_fingerprint(country_code: str) -> Dict:
    """
    Generate a complete browser fingerprint for specified country
    """
    config = COUNTRY_CONFIGS.get(country_code.lower(), COUNTRY_CONFIGS['us'])
    
    # Select random User Agent
    user_agent = random.choice(USER_AGENTS)
    is_mac = "Macintosh" in user_agent
    is_windows = "Windows" in user_agent
    
    # Determine platform
    if is_mac:
        platform = "MacIntel"
        vendor = "Apple Computer, Inc."
        fonts = random.sample(MAC_FONTS, min(len(MAC_FONTS), random.randint(12, 18)))
    else:
        platform = "Win32"
        vendor = "Google Inc."
        fonts = random.sample(WINDOWS_FONTS, min(len(WINDOWS_FONTS), random.randint(14, 20)))
    
    # Screen resolution
    screen_width, screen_height = random.choice(SCREEN_RESOLUTIONS)
    
    # WebGL
    webgl_vendor, webgl_renderer = random.choice(WEBGL_RENDERERS)
    if is_mac:
        webgl_vendor, webgl_renderer = random.choice([r for r in WEBGL_RENDERERS if "Apple" in r[0]])
    elif is_windows:
        webgl_vendor, webgl_renderer = random.choice([r for r in WEBGL_RENDERERS if "Apple" not in r[0]])
    
    # Hardware
    hardware_concurrency = random.choice([4, 6, 8, 12, 16])
    device_memory = random.choice([4, 8, 16, 32])
    
    fingerprint = {
        # Basic browser info
        "userAgent": user_agent,
        "platform": platform,
        "vendor": vendor,
        "language": config['language'],
        "languages": config['languages'],
        
        # Screen
        "screenWidth": screen_width,
        "screenHeight": screen_height,
        "availWidth": screen_width,
        "availHeight": screen_height - random.randint(30, 80),  # Taskbar
        "colorDepth": 24,
        "pixelRatio": random.choice([1, 1.25, 1.5, 2]),
        
        # Timezone
        "timezone": config['timezone'],
        "timezoneOffset": config['timezone_offset'],
        
        # Hardware
        "hardwareConcurrency": hardware_concurrency,
        "deviceMemory": device_memory,
        
        # WebGL
        "webglVendor": webgl_vendor,
        "webglRenderer": webgl_renderer,
        
        # Canvas (unique noise for each fingerprint)
        "canvasNoiseSeed": generate_canvas_noise_seed(),
        
        # Audio
        "audioContextHash": generate_audio_hash(),
        
        # Fonts
        "fonts": fonts,
        
        # Plugins (Chrome typical)
        "plugins": [
            {"name": "Chrome PDF Plugin", "filename": "internal-pdf-viewer"},
            {"name": "Chrome PDF Viewer", "filename": "mhjfbmdgcfjbbpaeojofohoefgiehjai"},
            {"name": "Native Client", "filename": "internal-nacl-plugin"},
        ],
        
        # Additional params
        "doNotTrack": None,
        "cookieEnabled": True,
        "webdriver": False,  # CRITICAL: Must be False!
        
        # Touch support (desktop = no touch)
        "maxTouchPoints": 0,
        
        # Country specific
        "countryCode": country_code.upper(),
        "countryName": config['name'],
    }
    
    return fingerprint


def generate_fingerprints_batch(country_code: str, count: int) -> List[Dict]:
    """Generate multiple unique fingerprints for a country"""
    fingerprints = []
    
    for _ in range(count):
        fp = generate_fingerprint(country_code)
        fingerprints.append(fp)
    
    return fingerprints


def get_chrome_args_from_fingerprint(fingerprint: Dict) -> List[str]:
    """
    Convert fingerprint to Chrome launch arguments
    """
    args = [
        f"--window-size={fingerprint['screenWidth']},{fingerprint['screenHeight']}",
        f"--lang={fingerprint['language']}",
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-popup-blocking",
    ]
    
    return args


def get_timezone_for_country(country_code: str) -> str:
    """Get timezone for country code"""
    config = COUNTRY_CONFIGS.get(country_code.lower(), COUNTRY_CONFIGS['us'])
    return config['timezone']


# JavaScript to inject for fingerprint spoofing
FINGERPRINT_INJECTION_JS = """
(function() {
    // Spoof navigator properties
    const fp = %FINGERPRINT%;
    
    // Override webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => false
    });
    
    // Override platform
    Object.defineProperty(navigator, 'platform', {
        get: () => fp.platform
    });
    
    // Override languages
    Object.defineProperty(navigator, 'languages', {
        get: () => fp.languages
    });
    
    // Override hardware concurrency
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => fp.hardwareConcurrency
    });
    
    // Override device memory
    Object.defineProperty(navigator, 'deviceMemory', {
        get: () => fp.deviceMemory
    });
    
    // Canvas fingerprint noise
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {
        if (type === 'image/png' || type === undefined) {
            const ctx = this.getContext('2d');
            if (ctx) {
                const imageData = ctx.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    // Add tiny noise based on seed
                    imageData.data[i] = imageData.data[i] ^ (fp.canvasNoiseSeed % 3);
                }
                ctx.putImageData(imageData, 0, 0);
            }
        }
        return originalToDataURL.apply(this, arguments);
    };
    
    // WebGL spoofing
    const getParameterProxyHandler = {
        apply: function(target, thisArg, args) {
            const param = args[0];
            const gl = thisArg;
            
            // UNMASKED_VENDOR_WEBGL
            if (param === 37445) {
                return fp.webglVendor;
            }
            // UNMASKED_RENDERER_WEBGL  
            if (param === 37446) {
                return fp.webglRenderer;
            }
            
            return Reflect.apply(target, thisArg, args);
        }
    };
    
    // Apply to WebGL
    const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = new Proxy(originalGetParameter, getParameterProxyHandler);
    
    if (typeof WebGL2RenderingContext !== 'undefined') {
        const originalGetParameter2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = new Proxy(originalGetParameter2, getParameterProxyHandler);
    }
    
    console.log('[Fingerprint] Spoofing applied successfully');
})();
"""


def get_fingerprint_injection_script(fingerprint: Dict) -> str:
    """Get JavaScript code to inject fingerprint spoofing"""
    fp_json = json.dumps(fingerprint)
    return FINGERPRINT_INJECTION_JS.replace('%FINGERPRINT%', fp_json)


if __name__ == "__main__":
    # Test fingerprint generation
    print("🔧 Testing Fingerprint Generator\n")
    
    for country in ['us', 'gb', 'de']:
        fp = generate_fingerprint(country)
        print(f"{'='*50}")
        print(f"🌍 Country: {fp['countryName']} ({country.upper()})")
        print(f"   User-Agent: {fp['userAgent'][:60]}...")
        print(f"   Platform: {fp['platform']}")
        print(f"   Screen: {fp['screenWidth']}x{fp['screenHeight']}")
        print(f"   Timezone: {fp['timezone']}")
        print(f"   Language: {fp['language']}")
        print(f"   WebGL: {fp['webglRenderer'][:50]}...")
        print(f"   Canvas Seed: {fp['canvasNoiseSeed']}")
        print()
