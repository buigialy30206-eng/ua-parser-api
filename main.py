"""
User Agent Parser API
Parse User-Agent strings into browser, OS, device info.
Pure Python, no external APIs.
"""

import re
from typing import Optional

from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="User Agent Parser API", version="1.0.0", dependencies=[Depends(_rate_limit)])
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
import time as _t, threading as _th
_rl_win, _rl_max, _rl_hits, _rl_lk = 60, 60, {}, _th.Lock()

async def _rate_limit(request):
    from fastapi import Request, HTTPException
    ip = (request.headers.get('X-Forwarded-For','') or request.headers.get('X-Real-IP','') or (request.client.host if request.client else '127.0.0.1')).split(',')[0].strip()
    now = _t.time()
    with _rl_lk:
        e = _rl_hits.get(ip)
        if e:
            if now - e['s'] > _rl_win: e['s'], e['c'] = now, 1
            else:
                e['c'] += 1
                if e['c'] > _rl_max: raise HTTPException(429, 'Too many requests')
        else: _rl_hits[ip] = {'s': now, 'c': 1}
    return True

@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "ok"}



class UAResult(BaseModel):
    browser: str = "Unknown"
    browser_version: str = ""
    os: str = "Unknown"
    os_version: str = ""
    device: str = "Desktop"
    is_mobile: bool = False
    is_tablet: bool = False
    is_bot: bool = False


BROWSER_PATTERNS = [
    (r"Edg/([\d.]+)", "Edge"),
    (r"Chrome/([\d.]+)", "Chrome"),
    (r"Firefox/([\d.]+)", "Firefox"),
    (r"Safari/([\d.]+)", "Safari"),
    (r"OPR/([\d.]+)", "Opera"),
    (r"MSIE ([\d.]+)", "IE"),
    (r"Trident/.*rv:([\d.]+)", "IE"),
]

OS_PATTERNS = [
    (r"Windows NT ([\d.]+)", "Windows"),
    (r"Mac OS X ([\d._]+)", "macOS"),
    (r"Linux", "Linux"),
    (r"Android ([\d.]+)", "Android"),
    (r"iPhone OS ([\d_]+)", "iOS"),
    (r"iPad.*OS ([\d_]+)", "iPadOS"),
    (r"CrOS", "ChromeOS"),
]


@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"service": "User Agent Parser API", "version": "1.0.0"}


@app.get("/parse", response_model=UAResult)
async def parse(ua: str = Query(..., description="User-Agent string to parse")):
    result = UAResult()
    result.is_bot = bool(re.search(r"bot|crawler|spider|scraper", ua, re.I))

    # Browser
    for pattern, name in BROWSER_PATTERNS:
        m = re.search(pattern, ua)
        if m:
            result.browser = name
            result.browser_version = m.group(1)
            break

    # OS
    for pattern, name in OS_PATTERNS:
        m = re.search(pattern, ua)
        if m:
            result.os = name
            result.os_version = m.group(1).replace("_", ".") if m.lastindex else ""
            break

    # Device
    if "iPhone" in ua or "iPod" in ua:
        result.device = "Phone"
        result.is_mobile = True
    elif "iPad" in ua:
        result.device = "Tablet"
        result.is_tablet = True
    elif "Android" in ua and "Mobile" in ua:
        result.device = "Phone"
        result.is_mobile = True
    elif "Android" in ua:
        result.device = "Tablet"
        result.is_tablet = True

    return result
