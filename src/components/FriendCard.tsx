"use client";

import { Friend } from "@/lib/types";
import { avatarColors } from "@/lib/data";

interface FriendCardProps {
  friend: Friend;
  onRemove?: (id: string) => void;
  onMessage?: (id: string) => void;
}

const statusColors = {
  online: "bg-green-500",
  "in-game": "bg-blue-500",
  idle: "bg-yellow-500",
  offline: "bg-gray-500",
};

const statusLabels = {
  online: "Online",
  "in-game": "In Game",
  idle: "Idle",
  offline: "Offline",
};

export default function FriendCard({ friend, onRemove, onMessage }: FriendCardProps) {
  const avatarColor = avatarColors[friend.avatar] || "bg-primary";

  return (
    <div className="card-glow bg-dark-800 rounded-xl p-4 border border-dark-600 flex items-center gap-4">
      {/* Avatar */}
      <div className="relative shrink-0">
        <div className={`w-12 h-12 rounded-full ${avatarColor} flex items-center justify-center text-lg font-bold text-white`}>
          {friend.username[0]}
        </div>
        <div className={`absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 ${statusColors[friend.status]} rounded-full border-2 border-dark-800`} />
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <h3 className="font-semibold text-sm truncate">{friend.username}</h3>
        <div className="flex items-center gap-1.5 mt-0.5">
          <span className={`text-xs ${friend.status === "online" ? "text-green-400" : friend.status === "in-game" ? "text-blue-400" : friend.status === "idle" ? "text-yellow-400" : "text-gray-500"}`}>
            {statusLabels[friend.status]}
          </span>
          {friend.currentGame && (
            <span className="text-xs text-gray-500">- {friend.currentGame}</span>
          )}
          {friend.status === "offline" && friend.lastSeen && (
            <span className="text-xs text-gray-600">- {friend.lastSeen}</span>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2 shrink-0">
        {onMessage && (
          <button
            onClick={() => onMessage(friend.id)}
            className="p-2 rounded-lg hover:bg-dark-600 transition-colors text-gray-400 hover:text-accent"
            title="Message"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </button>
        )}
        {onRemove && (
          <button
            onClick={() => onRemove(friend.id)}
            className="p-2 rounded-lg hover:bg-dark-600 transition-colors text-gray-400 hover:text-danger"
            title="Remove friend"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7a4 4 0 11-8 0 4 4 0 018 0zM9 14a6 6 0 00-6 6v1h12v-1a6 6 0 00-6-6zM21 12h-6" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
