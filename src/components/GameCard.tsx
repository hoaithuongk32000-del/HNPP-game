"use client";

import Link from "next/link";
import { Game } from "@/lib/types";
import { gameColors } from "@/lib/data";

interface GameCardProps {
  game: Game;
}

export default function GameCard({ game }: GameCardProps) {
  const gradient = gameColors[game.thumbnail] || "from-primary to-accent";

  return (
    <Link href={`/games/${game.id}`}>
      <div className="card-glow bg-dark-800 rounded-xl overflow-hidden border border-dark-600 cursor-pointer group">
        {/* Thumbnail */}
        <div className={`relative h-40 bg-gradient-to-br ${gradient} flex items-center justify-center overflow-hidden`}>
          <div className="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition-colors" />
          <span className="text-4xl font-bold text-white/80 group-hover:scale-110 transition-transform">
            {game.title.split(" ").map((w) => w[0]).join("").slice(0, 3)}
          </span>
          {game.featured && (
            <div className="absolute top-2 left-2 bg-warning text-dark-900 text-[10px] font-bold px-2 py-0.5 rounded-full">
              FEATURED
            </div>
          )}
          <div className="absolute bottom-2 right-2 bg-black/60 backdrop-blur text-xs px-2 py-0.5 rounded-full flex items-center gap-1">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
            {game.players.toLocaleString()} playing
          </div>
        </div>

        {/* Info */}
        <div className="p-3">
          <h3 className="font-semibold text-sm mb-1 truncate group-hover:text-primary-light transition-colors">
            {game.title}
          </h3>
          <p className="text-xs text-gray-400 line-clamp-2 mb-2">{game.description}</p>
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">{game.creator}</span>
            <div className="flex items-center gap-1">
              <svg className="w-3 h-3 text-warning" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              <span className="text-xs text-gray-400">{game.rating}</span>
            </div>
          </div>
          <div className="flex gap-1 mt-2 flex-wrap">
            {game.tags.slice(0, 3).map((tag) => (
              <span key={tag} className="text-[10px] bg-dark-600 text-gray-400 px-1.5 py-0.5 rounded">
                #{tag}
              </span>
            ))}
          </div>
        </div>
      </div>
    </Link>
  );
}
