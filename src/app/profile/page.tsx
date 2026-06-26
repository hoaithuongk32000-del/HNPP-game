"use client";

import { useState } from "react";
import { currentUser, games } from "@/lib/data";

export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState<"overview" | "games" | "badges" | "settings">("overview");
  const [bio, setBio] = useState(currentUser.bio);
  const [isEditingBio, setIsEditingBio] = useState(false);

  const xpPercentage = (currentUser.xp / currentUser.xpToNext) * 100;
  const recentGames = games.slice(0, 6);

  return (
    <div className="p-4 lg:p-6">
      {/* Profile Header */}
      <div className="relative bg-dark-800 rounded-2xl overflow-hidden border border-dark-600 mb-6">
        {/* Banner */}
        <div className="h-32 bg-gradient-to-r from-primary via-accent to-primary opacity-30" />

        <div className="px-6 pb-6 -mt-12 relative">
          <div className="flex flex-col sm:flex-row sm:items-end gap-4">
            {/* Avatar */}
            <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-primary to-accent flex items-center justify-center text-3xl font-bold text-white border-4 border-dark-800 shadow-xl">
              {currentUser.username[0]}
            </div>

            <div className="flex-1">
              <h1 className="text-2xl font-bold">{currentUser.username}</h1>
              <div className="flex items-center gap-4 mt-1">
                <span className="text-accent font-semibold">Level {currentUser.level}</span>
                <span className="text-gray-500 text-sm">Joined {new Date(currentUser.joinDate).toLocaleDateString()}</span>
              </div>
            </div>

            <button className="btn-primary text-sm">Edit Profile</button>
          </div>

          {/* XP Bar */}
          <div className="mt-4">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>XP: {currentUser.xp.toLocaleString()} / {currentUser.xpToNext.toLocaleString()}</span>
              <span>Level {currentUser.level + 1}</span>
            </div>
            <div className="w-full bg-dark-600 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-primary to-accent transition-all"
                style={{ width: `${xpPercentage}%` }}
              />
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mt-4">
            <div className="bg-dark-700 rounded-xl p-3 text-center">
              <p className="text-xl font-bold text-primary-light">{currentUser.gamesPlayed}</p>
              <p className="text-xs text-gray-500">Games Played</p>
            </div>
            <div className="bg-dark-700 rounded-xl p-3 text-center">
              <p className="text-xl font-bold text-accent">{currentUser.friends}</p>
              <p className="text-xs text-gray-500">Friends</p>
            </div>
            <div className="bg-dark-700 rounded-xl p-3 text-center">
              <p className="text-xl font-bold text-warning">{currentUser.badges.length}</p>
              <p className="text-xs text-gray-500">Badges</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-dark-800 rounded-lg p-1 mb-6 w-fit">
        {(["overview", "games", "badges", "settings"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all capitalize ${
              activeTab === tab
                ? "bg-primary text-white"
                : "text-gray-400 hover:text-white hover:bg-dark-600"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Bio */}
          <div className="bg-dark-800 rounded-xl p-5 border border-dark-600">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold">About Me</h3>
              <button
                onClick={() => setIsEditingBio(!isEditingBio)}
                className="text-xs text-primary-light hover:text-primary transition-colors"
              >
                {isEditingBio ? "Save" : "Edit"}
              </button>
            </div>
            {isEditingBio ? (
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                className="w-full bg-dark-700 border border-dark-500 rounded-lg p-3 text-sm focus:outline-none focus:border-primary resize-none h-24"
              />
            ) : (
              <p className="text-sm text-gray-300">{bio}</p>
            )}
          </div>

          {/* Badges Preview */}
          <div className="bg-dark-800 rounded-xl p-5 border border-dark-600">
            <h3 className="font-semibold mb-3">Badges</h3>
            <div className="flex flex-wrap gap-3">
              {currentUser.badges.map((badge) => (
                <div key={badge.id} className="flex items-center gap-2 bg-dark-700 rounded-lg px-3 py-2">
                  <span className="text-xl">{badge.icon}</span>
                  <div>
                    <p className="text-xs font-medium">{badge.name}</p>
                    <p className="text-[10px] text-gray-500">{badge.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-dark-800 rounded-xl p-5 border border-dark-600 lg:col-span-2">
            <h3 className="font-semibold mb-3">Recently Played</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {recentGames.map((game) => (
                <div key={game.id} className="bg-dark-700 rounded-lg p-3 text-center hover:bg-dark-600 transition-colors cursor-pointer">
                  <div className="w-12 h-12 mx-auto rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center text-lg font-bold mb-2">
                    {game.title[0]}
                  </div>
                  <p className="text-xs font-medium truncate">{game.title}</p>
                  <p className="text-[10px] text-gray-500 mt-0.5">{Math.floor(Math.random() * 10) + 1}h played</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === "games" && (
        <div>
          <h2 className="font-semibold text-lg mb-4">My Games</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentGames.map((game) => (
              <div key={game.id} className="bg-dark-800 rounded-xl p-4 border border-dark-600 card-glow">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center font-bold">
                    {game.title[0]}
                  </div>
                  <div>
                    <p className="font-medium text-sm">{game.title}</p>
                    <p className="text-xs text-gray-500">{game.category}</p>
                  </div>
                </div>
                <div className="flex justify-between text-xs text-gray-500">
                  <span>{Math.floor(Math.random() * 20) + 1}h total</span>
                  <span>Last played {Math.floor(Math.random() * 7) + 1}d ago</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "badges" && (
        <div>
          <h2 className="font-semibold text-lg mb-4">All Badges</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {currentUser.badges.map((badge) => (
              <div key={badge.id} className="bg-dark-800 rounded-xl p-5 border border-dark-600 text-center card-glow">
                <span className="text-4xl block mb-3">{badge.icon}</span>
                <h3 className="font-semibold mb-1">{badge.name}</h3>
                <p className="text-xs text-gray-500">{badge.description}</p>
                <p className="text-[10px] text-accent mt-2">Earned</p>
              </div>
            ))}
            {/* Locked badges */}
            {[
              { name: "Speed Demon", icon: "⚡", desc: "Complete a race in under 30 seconds" },
              { name: "Team Player", icon: "🤝", desc: "Play 20 cooperative games" },
              { name: "Explorer", icon: "🗺️", desc: "Visit all game worlds" },
            ].map((badge, i) => (
              <div key={i} className="bg-dark-800 rounded-xl p-5 border border-dark-600 text-center opacity-50">
                <span className="text-4xl block mb-3 grayscale">{badge.icon}</span>
                <h3 className="font-semibold mb-1">{badge.name}</h3>
                <p className="text-xs text-gray-500">{badge.desc}</p>
                <p className="text-[10px] text-gray-600 mt-2">Locked</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "settings" && (
        <div className="max-w-2xl space-y-4">
          <div className="bg-dark-800 rounded-xl p-5 border border-dark-600">
            <h3 className="font-semibold mb-4">Account Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Username</label>
                <input
                  type="text"
                  defaultValue={currentUser.username}
                  className="w-full bg-dark-700 border border-dark-500 rounded-lg py-2 px-3 text-sm focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Email</label>
                <input
                  type="email"
                  defaultValue="player@hnppgame.com"
                  className="w-full bg-dark-700 border border-dark-500 rounded-lg py-2 px-3 text-sm focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Bio</label>
                <textarea
                  defaultValue={currentUser.bio}
                  className="w-full bg-dark-700 border border-dark-500 rounded-lg p-3 text-sm focus:outline-none focus:border-primary resize-none h-20"
                />
              </div>
              <button className="btn-primary">Save Changes</button>
            </div>
          </div>

          <div className="bg-dark-800 rounded-xl p-5 border border-dark-600">
            <h3 className="font-semibold mb-4">Privacy</h3>
            <div className="space-y-3">
              {["Show online status", "Allow friend requests", "Show game activity"].map((setting) => (
                <label key={setting} className="flex items-center justify-between cursor-pointer">
                  <span className="text-sm text-gray-300">{setting}</span>
                  <div className="relative">
                    <input type="checkbox" defaultChecked className="sr-only peer" />
                    <div className="w-10 h-5 bg-dark-600 rounded-full peer-checked:bg-primary transition-colors" />
                    <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full peer-checked:translate-x-5 transition-transform" />
                  </div>
                </label>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
