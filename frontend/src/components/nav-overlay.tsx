"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

const NAV_ITEMS = [
  { label: "DASHBOARD",  href: "/dashboard" },
  { label: "STRATEGIES", href: "/strategies" },
  { label: "RISK",       href: "/risk" },
  { label: "SIGNALS",    href: "#signals" },
];

export default function NavOverlay() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled]   = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 48);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // lock body scroll when mobile menu is open
  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [menuOpen]);

  return (
    <>
      <nav
        className="nav-overlay"
        style={{
          background: scrolled
            ? "rgba(0,0,0,0.72)"
            : "transparent",
          backdropFilter: scrolled ? "blur(12px)" : "none",
          transition: "background 0.3s ease, backdrop-filter 0.3s ease",
        }}
        aria-label="Main navigation"
      >
        {/* Logo */}
        <Link
          href="/"
          className="button-cap"
          style={{ color: "#fff", textDecoration: "none", letterSpacing: "1.17px" }}
          aria-label="TradeAI home"
        >
          TRADEAI
        </Link>

        {/* Desktop nav items */}
        <ul
          className="hidden tablet:flex items-center gap-8 list-none"
          role="list"
        >
          {NAV_ITEMS.map((item) => (
            <li key={item.label}>
              <Link
                href={item.href}
                className="micro-cap"
                style={{
                  color: "#fff",
                  textDecoration: "none",
                  opacity: 0.85,
                  transition: "opacity 0.2s ease",
                }}
                onMouseEnter={(e) =>
                  ((e.target as HTMLElement).style.opacity = "1")
                }
                onMouseLeave={(e) =>
                  ((e.target as HTMLElement).style.opacity = "0.85")
                }
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>

        {/* Desktop CTA */}
        <Link
          href="/dashboard"
          className="btn-ghost-dark hidden tablet:inline-flex"
        >
          LAUNCH APP
        </Link>

        {/* Hamburger — mobile only */}
        <button
          className="tablet:hidden flex flex-col justify-center items-center w-10 h-10 gap-[6px]"
          onClick={() => setMenuOpen((o) => !o)}
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          aria-expanded={menuOpen}
          style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}
        >
          <span
            style={{
              display: "block",
              width: "22px",
              height: "1px",
              background: "#fff",
              transition: "transform 0.25s ease",
              transform: menuOpen ? "translateY(7px) rotate(45deg)" : "none",
            }}
          />
          <span
            style={{
              display: "block",
              width: "22px",
              height: "1px",
              background: "#fff",
              opacity: menuOpen ? 0 : 1,
              transition: "opacity 0.2s ease",
            }}
          />
          <span
            style={{
              display: "block",
              width: "22px",
              height: "1px",
              background: "#fff",
              transition: "transform 0.25s ease",
              transform: menuOpen ? "translateY(-7px) rotate(-45deg)" : "none",
            }}
          />
        </button>
      </nav>

      {/* Mobile menu drawer */}
      <div
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 49,
          background: "#000",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: "40px",
          opacity: menuOpen ? 1 : 0,
          pointerEvents: menuOpen ? "all" : "none",
          transition: "opacity 0.3s ease",
        }}
        aria-hidden={!menuOpen}
      >
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.label}
            href={item.href}
            className="display-lg"
            style={{ color: "#fff", textDecoration: "none" }}
            onClick={() => setMenuOpen(false)}
          >
            {item.label}
          </Link>
        ))}
        <Link
          href="/dashboard"
          className="btn-ghost-dark"
          style={{ marginTop: "8px" }}
          onClick={() => setMenuOpen(false)}
        >
          LAUNCH APP
        </Link>
      </div>
    </>
  );
}
