import os

def create_demo_assets():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    uploads_demo = os.path.join(base_dir, "uploads", "demo")
    frontend_demo = os.path.join(base_dir, "frontend", "assets", "demo_images")
    
    os.makedirs(uploads_demo, exist_ok=True)
    os.makedirs(frontend_demo, exist_ok=True)

    svgs = {
        "avatar_dr_zhang.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <defs>
    <linearGradient id="bg-dr" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e3a8a"/>
      <stop offset="100%" stop-color="#3b82f6"/>
    </linearGradient>
  </defs>
  <circle cx="60" cy="60" r="56" fill="url(#bg-dr)" stroke="#60a5fa" stroke-width="4"/>
  <circle cx="60" cy="48" r="22" fill="#fde047"/>
  <path d="M40 40 Q60 20 80 40 Q75 30 60 30 Q45 30 40 40 Z" fill="#1e293b"/>
  <rect x="44" y="43" width="13" height="10" rx="2" fill="none" stroke="#0f172a" stroke-width="2.5"/>
  <rect x="63" y="43" width="13" height="10" rx="2" fill="none" stroke="#0f172a" stroke-width="2.5"/>
  <line x1="57" y1="48" x2="63" y2="48" stroke="#0f172a" stroke-width="2.5"/>
  <path d="M32 96 C34 78 48 72 60 72 C72 72 86 78 88 96 Z" fill="#ffffff"/>
  <path d="M54 72 L60 84 L66 72 Z" fill="#0284c7"/>
  <circle cx="88" cy="88" r="16" fill="#10b981" stroke="#ffffff" stroke-width="2"/>
  <text x="88" y="92" font-family="sans-serif" font-size="10" font-weight="bold" fill="#ffffff" text-anchor="middle">Dr</text>
</svg>""",

        "avatar_li_quality.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <defs>
    <linearGradient id="bg-li" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#047857"/>
      <stop offset="100%" stop-color="#10b981"/>
    </linearGradient>
  </defs>
  <circle cx="60" cy="60" r="56" fill="url(#bg-li)" stroke="#34d399" stroke-width="4"/>
  <circle cx="60" cy="48" r="22" fill="#fbcfe8"/>
  <path d="M38 46 Q60 18 82 46 Q70 26 60 26 Q50 26 38 46 Z" fill="#334155"/>
  <path d="M32 96 C34 78 48 72 60 72 C72 72 86 78 88 96 Z" fill="#f1f5f9"/>
  <circle cx="88" cy="88" r="16" fill="#059669" stroke="#ffffff" stroke-width="2"/>
  <text x="88" y="92" font-family="sans-serif" font-size="9" font-weight="bold" fill="#ffffff" text-anchor="middle">QA</text>
</svg>""",

        "avatar_wang_pe.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <defs>
    <linearGradient id="bg-pe" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#7c3aed"/>
      <stop offset="100%" stop-color="#a855f7"/>
    </linearGradient>
  </defs>
  <circle cx="60" cy="60" r="56" fill="url(#bg-pe)" stroke="#c084fc" stroke-width="4"/>
  <circle cx="60" cy="48" r="22" fill="#fed7aa"/>
  <path d="M38 42 Q60 22 82 42 Z" fill="#1e293b"/>
  <path d="M36 46 Q34 34 60 32 Q86 34 84 46" fill="none" stroke="#38bdf8" stroke-width="3"/>
  <circle cx="35" cy="52" r="5" fill="#0284c7"/>
  <path d="M32 96 C34 78 48 72 60 72 C72 72 86 78 88 96 Z" fill="#1e293b"/>
  <circle cx="88" cy="88" r="16" fill="#9333ea" stroke="#ffffff" stroke-width="2"/>
  <text x="88" y="92" font-family="sans-serif" font-size="9" font-weight="bold" fill="#ffffff" text-anchor="middle">PE</text>
</svg>""",

        "avatar_chen_gm.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <defs>
    <linearGradient id="bg-gm" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#334155"/>
    </linearGradient>
  </defs>
  <circle cx="60" cy="60" r="56" fill="url(#bg-gm)" stroke="#94a3b8" stroke-width="4"/>
  <circle cx="60" cy="48" r="22" fill="#fef08a"/>
  <path d="M38 42 Q60 22 82 42 Z" fill="#475569"/>
  <path d="M32 96 C34 78 48 72 60 72 C72 72 86 78 88 96 Z" fill="#020617"/>
  <polygon points="58,74 62,74 64,88 60,94 56,88" fill="#ef4444"/>
  <circle cx="88" cy="88" r="16" fill="#eab308" stroke="#ffffff" stroke-width="2"/>
  <text x="88" y="92" font-family="sans-serif" font-size="9" font-weight="bold" fill="#0f172a" text-anchor="middle">GM</text>
</svg>""",

        "avatar_liu_qe.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <defs>
    <linearGradient id="bg-qe" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0284c7"/>
      <stop offset="100%" stop-color="#38bdf8"/>
    </linearGradient>
  </defs>
  <circle cx="60" cy="60" r="56" fill="url(#bg-qe)" stroke="#7dd3fc" stroke-width="4"/>
  <circle cx="60" cy="48" r="22" fill="#ffedd5"/>
  <path d="M38 42 Q60 22 82 42 Z" fill="#0f172a"/>
  <path d="M32 96 C34 78 48 72 60 72 C72 72 86 78 88 96 Z" fill="#0369a1"/>
  <circle cx="88" cy="88" r="16" fill="#0284c7" stroke="#ffffff" stroke-width="2"/>
  <text x="88" y="92" font-family="sans-serif" font-size="9" font-weight="bold" fill="#ffffff" text-anchor="middle">QE</text>
</svg>""",

        "avatar_default.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <circle cx="60" cy="60" r="56" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="4"/>
  <circle cx="60" cy="48" r="22" fill="#94a3b8"/>
  <path d="M32 96 C34 78 48 72 60 72 C72 72 86 78 88 96 Z" fill="#64748b"/>
</svg>""",

        "product_matrix_led.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 150" width="200" height="150">
  <defs>
    <linearGradient id="pbg-led" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#090d16"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="200" height="150" rx="8" fill="url(#pbg-led)"/>
  <path d="M20 95 C 40 50, 140 40, 180 65 L 175 105 C 130 115, 60 110, 20 95 Z" fill="#0f172a" stroke="#38bdf8" stroke-width="2.5"/>
  <circle cx="60" cy="80" r="14" fill="#0369a1" stroke="#67e8f9" stroke-width="2"/>
  <circle cx="60" cy="80" r="8" fill="#e0f2fe"/>
  <circle cx="100" cy="78" r="12" fill="#0369a1" stroke="#67e8f9" stroke-width="2"/>
  <circle cx="100" cy="78" r="6" fill="#e0f2fe"/>
  <circle cx="138" cy="75" r="10" fill="#0369a1" stroke="#67e8f9" stroke-width="2"/>
  <circle cx="138" cy="75" r="5" fill="#e0f2fe"/>
  <path d="M28 88 Q 80 54 172 68" fill="none" stroke="#38bdf8" stroke-width="4" stroke-linecap="round"/>
  <rect x="10" y="10" width="80" height="18" rx="4" fill="#0284c7" fill-opacity="0.4" stroke="#38bdf8" stroke-width="1"/>
  <text x="50" y="23" font-family="sans-serif" font-size="9" font-weight="bold" fill="#38bdf8" text-anchor="middle">HD-MATRIX 32</text>
</svg>""",

        "product_drl_module.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 150" width="200" height="150">
  <defs>
    <linearGradient id="pbg-drl" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#111827"/>
      <stop offset="100%" stop-color="#1f2937"/>
    </linearGradient>
  </defs>
  <rect width="200" height="150" rx="8" fill="url(#pbg-drl)"/>
  <rect x="25" y="45" width="150" height="65" rx="6" fill="#374151" stroke="#9ca3af" stroke-width="2"/>
  <line x1="45" y1="45" x2="45" y2="110" stroke="#1f2937" stroke-width="3"/>
  <line x1="75" y1="45" x2="75" y2="110" stroke="#1f2937" stroke-width="3"/>
  <line x1="105" y1="45" x2="105" y2="110" stroke="#1f2937" stroke-width="3"/>
  <line x1="135" y1="45" x2="135" y2="110" stroke="#1f2937" stroke-width="3"/>
  <path d="M20 75 Q 100 35 180 75" fill="none" stroke="#f59e0b" stroke-width="6" stroke-linecap="round"/>
  <path d="M20 75 Q 100 35 180 75" fill="none" stroke="#fef3c7" stroke-width="2" stroke-linecap="round"/>
  <rect x="10" y="10" width="85" height="18" rx="4" fill="#d97706" fill-opacity="0.3" stroke="#f59e0b" stroke-width="1"/>
  <text x="52" y="23" font-family="sans-serif" font-size="9" font-weight="bold" fill="#fbbf24" text-anchor="middle">DRL-SWEEP-02</text>
</svg>""",

        "product_taillight_bar.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 150" width="200" height="150">
  <defs>
    <linearGradient id="pbg-tail" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#180608"/>
      <stop offset="100%" stop-color="#2e0c10"/>
    </linearGradient>
  </defs>
  <rect width="200" height="150" rx="8" fill="url(#pbg-tail)"/>
  <path d="M15 80 Q 100 65 185 80 L 180 95 Q 100 82 20 95 Z" fill="#450a0a" stroke="#dc2626" stroke-width="2"/>
  <path d="M20 86 Q 100 72 180 86" fill="none" stroke="#ef4444" stroke-width="5" stroke-linecap="round"/>
  <path d="M20 86 Q 100 72 180 86" fill="none" stroke="#fecaca" stroke-width="1.5" stroke-linecap="round"/>
  <rect x="10" y="10" width="80" height="18" rx="4" fill="#b91c1c" fill-opacity="0.3" stroke="#ef4444" stroke-width="1"/>
  <text x="50" y="23" font-family="sans-serif" font-size="9" font-weight="bold" fill="#fca5a5" text-anchor="middle">OLED-TAIL-3D</text>
</svg>""",

        "product_driver_board.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 150" width="200" height="150">
  <defs>
    <linearGradient id="pbg-pcb" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#064e3b"/>
      <stop offset="100%" stop-color="#022c22"/>
    </linearGradient>
  </defs>
  <rect width="200" height="150" rx="8" fill="url(#pbg-pcb)"/>
  <rect x="25" y="35" width="150" height="85" rx="4" fill="#047857" stroke="#10b981" stroke-width="2"/>
  <rect x="75" y="55" width="50" height="45" rx="2" fill="#1e293b" stroke="#94a3b8" stroke-width="1.5"/>
  <text x="100" y="80" font-family="monospace" font-size="8" font-weight="bold" fill="#38bdf8" text-anchor="middle">CAN-FD</text>
  <line x1="40" y1="45" x2="75" y2="65" stroke="#fde047" stroke-width="1.5" stroke-dasharray="3,2"/>
  <line x1="40" y1="85" x2="75" y2="85" stroke="#fde047" stroke-width="1.5" stroke-dasharray="3,2"/>
  <line x1="125" y1="65" x2="160" y2="45" stroke="#fde047" stroke-width="1.5" stroke-dasharray="3,2"/>
  <line x1="125" y1="85" x2="160" y2="85" stroke="#fde047" stroke-width="1.5" stroke-dasharray="3,2"/>
  <rect x="10" y="10" width="85" height="18" rx="4" fill="#059669" fill-opacity="0.3" stroke="#10b981" stroke-width="1"/>
  <text x="52" y="23" font-family="sans-serif" font-size="9" font-weight="bold" fill="#6ee7b7" text-anchor="middle">ECU-MATRIX-DRV</text>
</svg>"""
    }

    for filename, content in svgs.items():
        p1 = os.path.join(uploads_demo, filename)
        p2 = os.path.join(frontend_demo, filename)
        with open(p1, "w", encoding="utf-8") as f:
            f.write(content.strip())
        with open(p2, "w", encoding="utf-8") as f:
            f.write(content.strip())

    print(f"Generated {len(svgs)} demo SVG assets successfully in uploads/demo and frontend/assets/demo_images!")

if __name__ == "__main__":
    create_demo_assets()
