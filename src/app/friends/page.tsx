"use client";

import { useState } from "react";
import FriendCard from "@/components/FriendCard";
import { friends as initialFriends } from "@/lib/data";
import { Friend } from "@/lib/types";

export default function FriendsPage() {
  const [friendList, setFriendList] = useState<Friend[]>(initialFriends);
  const [filter, setFilter] = useState<"all" | "online" | "in-game" | "offline">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);
  const [addUsername, setAddUsername] = useState("");
  const [pendingRequests] = useState([
    { id: "pr1", username: "NewPlayer123", avatar: "avatar1" },
    { id: "pr2", username: "GamerX2024", avatar: "avatar2" },
  ]);
  const [activeTab, setActiveTab] = useState<"friends" | "requests" | "find">("friends");
  const [notification, setNotification] = useState<string | null>(null);

  const filteredFriends = friendList.filter((friend) => {
    const matchesFilter =
      filter === "all" ||
      friend.status === filter ||
      (filter === "online" && (friend.status === "online" || friend.status === "idle"));
    const matchesSearch =
      searchQuery === "" || friend.username.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const onlineFriends = friendList.filter(
    (f) => f.status === "online" || f.status === "in-game" || f.status === "idle"
  );

  const showNotification = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 3000);
  };

  const handleRemoveFriend = (id: string) => {
    const friend = friendList.find((f) => f.id === id);
    setFriendList((prev) => prev.filter((f) => f.id !== id));
    showNotification(`Removed ${friend?.username || "friend"} from your friends list`);
  };

  const handleMessageFriend = (id: string) => {
    const friend = friendList.find((f) => f.id === id);
    showNotification(`Opening chat with ${friend?.username || "friend"}...`);
  };

  const handleAddFriend = () => {
    if (!addUsername.trim()) return;
    const newFriend: Friend = {
      id: `f${Date.now()}`,
      username: addUsername.trim(),
      avatar: `avatar${Math.floor(Math.random() * 12) + 1}`,
      status: "offline",
      lastSeen: "just now",
    };
    setFriendList((prev) => [...prev, newFriend]);
    setAddUsername("");
    setShowAddModal(false);
    showNotification(`Friend request sent to ${newFriend.username}!`);
  };

  const handleAcceptRequest = (username: string) => {
    const newFriend: Friend = {
      id: `f${Date.now()}`,
      username,
      avatar: `avatar${Math.floor(Math.random() * 12) + 1}`,
      status: "online",
    };
    setFriendList((prev) => [...prev, newFriend]);
    showNotification(`${username} is now your friend!`);
  };

  return (
    <div className="p-4 lg:p-6">
      {/* Notification */}
      {notification && (
        <div className="fixed top-20 right-4 z-50 bg-accent text-dark-900 px-4 py-2 rounded-lg text-sm font-medium animate-slide-in shadow-lg">
          {notification}
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold">Friends</h1>
          <p className="text-gray-500 text-sm mt-1">
            {onlineFriends.length} online out of {friendList.length} friends
          </p>
        </div>
        <button onClick={() => setShowAddModal(true)} className="btn-primary flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
          </svg>
          Add Friend
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-dark-800 rounded-lg p-1 mb-6 w-fit">
        {(["friends", "requests", "find"] as const).map((tab) => (
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
            {tab === "requests" && pendingRequests.length > 0 && (
              <span className="ml-1.5 bg-danger text-white text-[10px] px-1.5 py-0.5 rounded-full">
                {pendingRequests.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {activeTab === "friends" && (
        <>
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-3 mb-4">
            <input
              type="text"
              placeholder="Search friends..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-dark-700 border border-dark-500 rounded-lg py-2 px-3 text-sm focus:outline-none focus:border-primary flex-1 max-w-sm"
            />
            <div className="flex gap-2">
              {(["all", "online", "in-game", "offline"] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-3 py-2 rounded-lg text-xs font-medium transition-all capitalize ${
                    filter === f
                      ? "bg-primary/20 text-primary-light border border-primary/30"
                      : "bg-dark-700 text-gray-400 hover:bg-dark-600"
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          {/* Friends List */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {filteredFriends.map((friend) => (
              <FriendCard
                key={friend.id}
                friend={friend}
                onRemove={handleRemoveFriend}
                onMessage={handleMessageFriend}
              />
            ))}
          </div>

          {filteredFriends.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <p>No friends found matching your criteria</p>
            </div>
          )}
        </>
      )}

      {activeTab === "requests" && (
        <div className="space-y-3">
          <h2 className="font-semibold text-lg mb-4">Pending Friend Requests</h2>
          {pendingRequests.map((req) => (
            <div key={req.id} className="bg-dark-800 rounded-xl p-4 border border-dark-600 flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-lg font-bold">
                {req.username[0]}
              </div>
              <div className="flex-1">
                <p className="font-semibold">{req.username}</p>
                <p className="text-xs text-gray-500">Wants to be your friend</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleAcceptRequest(req.username)}
                  className="px-4 py-2 bg-accent text-dark-900 text-sm font-medium rounded-lg hover:bg-accent-light transition-colors"
                >
                  Accept
                </button>
                <button className="px-4 py-2 bg-dark-600 text-gray-400 text-sm font-medium rounded-lg hover:bg-dark-500 transition-colors">
                  Decline
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === "find" && (
        <div>
          <h2 className="font-semibold text-lg mb-4">Find New Friends</h2>
          <div className="flex gap-3 mb-6">
            <input
              type="text"
              placeholder="Enter username to search..."
              className="bg-dark-700 border border-dark-500 rounded-lg py-2 px-3 text-sm focus:outline-none focus:border-primary flex-1 max-w-md"
            />
            <button className="btn-primary">Search</button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {["GalacticHero", "CyberNinja2025", "QuantumRacer", "PixelArtist"].map((name) => (
              <div key={name} className="bg-dark-800 rounded-xl p-4 border border-dark-600 flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-accent to-primary flex items-center justify-center text-lg font-bold">
                  {name[0]}
                </div>
                <div className="flex-1">
                  <p className="font-semibold">{name}</p>
                  <p className="text-xs text-gray-500">Level {Math.floor(Math.random() * 30) + 1}</p>
                </div>
                <button className="px-4 py-2 bg-primary text-white text-sm font-medium rounded-lg hover:bg-primary-light transition-colors">
                  Add Friend
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add Friend Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-dark-800 rounded-2xl p-6 w-full max-w-md border border-dark-600 animate-slide-in">
            <h2 className="text-lg font-bold mb-4">Add Friend</h2>
            <p className="text-sm text-gray-400 mb-4">Enter the username of the player you want to add as a friend.</p>
            <input
              type="text"
              placeholder="Username"
              value={addUsername}
              onChange={(e) => setAddUsername(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddFriend()}
              className="w-full bg-dark-700 border border-dark-500 rounded-lg py-2 px-3 text-sm focus:outline-none focus:border-primary mb-4"
              autoFocus
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => { setShowAddModal(false); setAddUsername(""); }}
                className="px-4 py-2 bg-dark-600 text-gray-400 rounded-lg hover:bg-dark-500 transition-colors text-sm"
              >
                Cancel
              </button>
              <button onClick={handleAddFriend} className="btn-primary">
                Send Request
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
