"use client";

import Link from "next/link";
import { useState } from "react";
import { currentUser } from "@/lib/data";

export default function Header() {
  const [searchQuery, setSearchQuery] = useState("");
  const [showNotifications, setShowNotifications] = useState(false);

  const notifications = [
    { id: 1, text: "ProGamer99 sent you a friend request", time: "2m ago" },
    { id: 2, text: "New game 'Space Explorer' is trending!", time: "15m ago" },
    { id: 3, text: "You earned the 'Champion' badge!", time: "1h ago" },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-primary/20">
      <div className="flex items-center justify-between px-4 h-16">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center font-bold text-white text-lg">
            H
          </div>
          <span className="text-xl font-bold neon-text hidden sm:block">
            HNPP GAME
          </span>
        </Link>

        {/* Search Bar */}
        <div className="flex-1 max-w-xl mx-4">
          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              placeholder="Search games, players..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-dark-700 border border-dark-500 rounded-full py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-primary transition-colors"
            />
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 rounded-lg hover:bg-dark-700 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
              <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-danger rounded-full text-[10px] flex items-center justify-center font-bold">
                3
              </span>
            </button>
            {showNotifications && (
              <div className="absolute right-0 top-12 w-80 glass rounded-xl p-3 animate-slide-in">
                <h3 className="font-semibold mb-2 text-sm">Notifications</h3>
                {notifications.map((n) => (
                  <div key={n.id} className="p-2 hover:bg-dark-600 rounded-lg cursor-pointer text-sm mb-1">
                    <p className="text-gray-200">{n.text}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{n.time}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* User */}
          <Link href="/profile" className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-dark-700 transition-colors">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-sm font-bold">
              {currentUser.username[0]}
            </div>
            <div className="hidden md:block">
              <p className="text-sm font-medium leading-tight">{currentUser.username}</p>
              <p className="text-xs text-accent">Lv.{currentUser.level}</p>
            </div>
          </Link>
        </div>
      </div>
    </header>
  );
}
