"use client";

import { useState } from "react";
import GameCard from "@/components/GameCard";
import { games, categories } from "@/lib/data";

export default function GamesPage() {
  const [activeCategory, setActiveCategory] = useState("All");
  const [sortBy, setSortBy] = useState<"popular" | "rating" | "newest">("popular");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredGames = games
    .filter((game) => {
      const matchesCategory = activeCategory === "All" || game.category === activeCategory;
      const matchesSearch =
        searchQuery === "" ||
        game.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        game.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesCategory && matchesSearch;
    })
    .sort((a, b) => {
      if (sortBy === "popular") return b.players - a.players;
      if (sortBy === "rating") return b.rating - a.rating;
      return 0;
    });

  return (
    <div className="p-4 lg:p-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold">Discover Games</h1>
          <p className="text-gray-500 text-sm mt-1">
            Browse {games.length} amazing games
          </p>
        </div>
        <div className="flex gap-3">
          <input
            type="text"
            placeholder="Search games..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-dark-700 border border-dark-500 rounded-lg py-2 px-3 text-sm focus:outline-none focus:border-primary w-64"
          />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as "popular" | "rating" | "newest")}
            className="bg-dark-700 border border-dark-500 rounded-lg py-2 px-3 text-sm focus:outline-none focus:border-primary"
          >
            <option value="popular">Most Popular</option>
            <option value="rating">Highest Rated</option>
            <option value="newest">Newest</option>
          </select>
        </div>
      </div>

      {/* Categories */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-all ${
              activeCategory === cat
                ? "bg-primary text-white shadow-lg shadow-primary/30"
                : "bg-dark-700 text-gray-400 hover:bg-dark-600 hover:text-white"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Results count */}
      <p className="text-sm text-gray-500 mb-4">{filteredGames.length} games found</p>

      {/* Game Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredGames.map((game) => (
          <GameCard key={game.id} game={game} />
        ))}
      </div>

      {filteredGames.length === 0 && (
        <div className="text-center py-16 text-gray-500">
          <p className="text-lg">No games found</p>
          <p className="text-sm mt-1">Try adjusting your filters</p>
        </div>
      )}
    </div>
  );
}
