"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { games, gameColors } from "@/lib/data";
import MiniGame3D from "@/components/MiniGame3D";

export default function GameDetailPage() {
  const params = useParams();
  const game = games.find((g) => g.id === params.id);

  if (!game) {
    return (
      <div className="p-6 text-center">
        <h1 className="text-2xl font-bold mb-4">Game not found</h1>
        <Link href="/games" className="btn-primary">
          Back to Games
        </Link>
      </div>
    );
  }

  const gradient = gameColors[game.thumbnail] || "from-primary to-accent";

  return (
    <div className="p-4 lg:p-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
        <Link href="/" className="hover:text-white transition-colors">Home</Link>
        <span>/</span>
        <Link href="/games" className="hover:text-white transition-colors">Games</Link>
        <span>/</span>
        <span className="text-gray-300">{game.title}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Game Area */}
        <div className="lg:col-span-2">
          <div className="w-full aspect-video rounded-xl overflow-hidden border border-dark-600">
            <MiniGame3D gameType={game.title} />
          </div>
        </div>

        {/* Game Info Sidebar */}
        <div className="space-y-4">
          {/* Title Card */}
          <div className="bg-dark-800 rounded-xl p-5 border border-dark-600">
            <div className={`w-full h-20 rounded-lg bg-gradient-to-r ${gradient} flex items-center justify-center mb-4`}>
              <span className="text-3xl font-bold text-white/80">
                {game.title.split(" ").map((w) => w[0]).join("").slice(0, 3)}
              </span>
            </div>
            <h1 className="text-xl font-bold mb-1">{game.title}</h1>
            <p className="text-sm text-gray-400 mb-3">by {game.creator}</p>
            <p className="text-sm text-gray-300 mb-4">{game.description}</p>

            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="bg-dark-700 rounded-lg p-3 text-center">
                <p className="text-lg font-bold text-accent">{game.players.toLocaleString()}</p>
                <p className="text-xs text-gray-500">Playing</p>
              </div>
              <div className="bg-dark-700 rounded-lg p-3 text-center">
                <p className="text-lg font-bold text-warning">{game.rating}</p>
                <p className="text-xs text-gray-500">Rating</p>
              </div>
              <div className="bg-dark-700 rounded-lg p-3 text-center">
                <p className="text-lg font-bold text-primary-light">{game.maxPlayers}</p>
                <p className="text-xs text-gray-500">Max Players</p>
              </div>
              <div className="bg-dark-700 rounded-lg p-3 text-center">
                <p className="text-lg font-bold text-green-400">{game.category}</p>
                <p className="text-xs text-gray-500">Category</p>
              </div>
            </div>

            <div className="flex flex-wrap gap-1.5 mb-4">
              {game.tags.map((tag) => (
                <span key={tag} className="text-xs bg-dark-600 text-gray-400 px-2 py-1 rounded">
                  #{tag}
                </span>
              ))}
            </div>

            <div className="flex gap-2">
              <button className="btn-accent flex-1">Add to Favorites</button>
              <button className="p-2 rounded-lg bg-dark-600 hover:bg-dark-500 transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                </svg>
              </button>
            </div>
          </div>

          {/* Chat */}
          <div className="bg-dark-800 rounded-xl p-4 border border-dark-600">
            <h3 className="font-semibold text-sm mb-3">Game Chat</h3>
            <div className="h-40 overflow-y-auto space-y-2 mb-3">
              {[
                { user: "ProGamer99", msg: "This game is awesome!", color: "text-red-400" },
                { user: "StarPlayer", msg: "Anyone wants to team up?", color: "text-green-400" },
                { user: "NightOwl", msg: "I found a secret area!", color: "text-blue-400" },
                { user: "GameWizard", msg: "GG everyone!", color: "text-purple-400" },
              ].map((chat, i) => (
                <div key={i} className="text-xs">
                  <span className={`font-semibold ${chat.color}`}>{chat.user}: </span>
                  <span className="text-gray-300">{chat.msg}</span>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Type a message..."
                className="flex-1 bg-dark-700 border border-dark-500 rounded-lg py-1.5 px-3 text-xs focus:outline-none focus:border-primary"
              />
              <button className="bg-primary hover:bg-primary-light text-white text-xs px-3 py-1.5 rounded-lg transition-colors">
                Send
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Related Games */}
      <section className="mt-8">
        <h2 className="text-lg font-bold mb-4">More {game.category} Games</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {games
            .filter((g) => g.category === game.category && g.id !== game.id)
            .slice(0, 4)
            .map((g) => (
              <Link key={g.id} href={`/games/${g.id}`}>
                <div className={`card-glow bg-dark-800 rounded-xl p-3 border border-dark-600 flex items-center gap-3`}>
                  <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${gameColors[g.thumbnail] || "from-primary to-accent"} flex items-center justify-center text-sm font-bold text-white/80 shrink-0`}>
                    {g.title[0]}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">{g.title}</p>
                    <p className="text-xs text-gray-500">{g.players.toLocaleString()} playing</p>
                  </div>
                </div>
              </Link>
            ))}
        </div>
      </section>
    </div>
  );
}
