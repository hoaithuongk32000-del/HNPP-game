"use client";

import { useState } from "react";
import GameCard from "@/components/GameCard";
import { games, categories } from "@/lib/data";

export default function Home() {
  const [activeCategory, setActiveCategory] = useState("All");
  const [searchFilter, setSearchFilter] = useState("");

  const filteredGames = games.filter((game) => {
    const matchesCategory = activeCategory === "All" || game.category === activeCategory;
    const matchesSearch =
      searchFilter === "" ||
      game.title.toLowerCase().includes(searchFilter.toLowerCase()) ||
      game.tags.some((t) => t.toLowerCase().includes(searchFilter.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  const featuredGames = games.filter((g) => g.featured);
  const totalPlayers = games.reduce((sum, g) => sum + g.players, 0);

  return (
    <div className="p-4 lg:p-6">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-dark-700 via-primary/20 to-dark-700 border border-primary/20 p-6 lg:p-8 mb-6">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(108,92,231,0.15),transparent_70%)]" />
        <div className="relative z-10">
          <h1 className="text-3xl lg:text-5xl font-bold mb-2">
            Welcome to <span className="neon-text">HNPP GAME</span>
          </h1>
          <p className="text-gray-400 text-lg mb-4">
            Play, Create, Connect - Your Gaming Universe
          </p>
          <div className="flex gap-6 text-sm">
            <div>
              <span className="text-2xl font-bold text-accent">{totalPlayers.toLocaleString()}</span>
              <p className="text-gray-500">Players Online</p>
            </div>
            <div>
              <span className="text-2xl font-bold text-primary-light">{games.length}</span>
              <p className="text-gray-500">Games Available</p>
            </div>
            <div>
              <span className="text-2xl font-bold text-warning">4.5</span>
              <p className="text-gray-500">Avg Rating</p>
            </div>
          </div>
        </div>
        <div className="absolute -right-10 -bottom-10 w-48 h-48 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute -right-5 -top-5 w-32 h-32 bg-accent/10 rounded-full blur-2xl" />
      </div>

      {/* Featured Games */}
      <section className="mb-8">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <span className="text-warning">&#9733;</span> Featured Games
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {featuredGames.map((game) => (
            <GameCard key={game.id} game={game} />
          ))}
        </div>
      </section>

      {/* All Games */}
      <section>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <h2 className="text-xl font-bold">All Games</h2>
          <input
            type="text"
            placeholder="Filter games..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="bg-dark-700 border border-dark-500 rounded-lg py-1.5 px-3 text-sm focus:outline-none focus:border-primary w-full sm:w-64"
          />
        </div>

        {/* Categories */}
        <div className="flex gap-2 mb-4 overflow-x-auto pb-2 scrollbar-hide">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`shrink-0 px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
                activeCategory === cat
                  ? "bg-primary text-white shadow-lg shadow-primary/30"
                  : "bg-dark-700 text-gray-400 hover:bg-dark-600 hover:text-white"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Game Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredGames.map((game) => (
            <GameCard key={game.id} game={game} />
          ))}
        </div>

        {filteredGames.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p>No games found. Try a different category or search term.</p>
          </div>
        )}
      </section>
    </div>
  );
}
