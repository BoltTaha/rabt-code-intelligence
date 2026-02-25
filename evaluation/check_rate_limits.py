#!/usr/bin/env python3
"""
Check your actual Gemini API rate limits
"""

import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ Error: GEMINI_API_KEY not set in .env")
    exit(1)

print("✅ API Key found")
print("")
print("📊 Check your actual rate limits:")
print("   https://aistudio.google.com/rate-limit")
print("")
print("Common free tier limits:")
print("   • 2 RPM (requests per minute) - very restricted")
print("   • 5 RPM - typical for free tier")
print("   • 15 RPM - higher free tier")
print("")
print("Our conservative settings:")
print("   • 15 second delay = 4 requests/minute")
print("   • Safe for even 5 RPM limits")
print("")
print("To test your limit:")
print("   1. Visit https://aistudio.google.com/rate-limit")
print("   2. Sign in with your API key account")
print("   3. View your current tier and limits")
