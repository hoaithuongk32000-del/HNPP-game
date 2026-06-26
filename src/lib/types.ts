export interface Game {
  id: string;
  title: string;
  description: string;
  thumbnail: string;
  category: string;
  players: number;
  maxPlayers: number;
  rating: number;
  creator: string;
  tags: string[];
  featured?: boolean;
}

export interface Friend {
  id: string;
  username: string;
  avatar: string;
  status: "online" | "offline" | "in-game" | "idle";
  currentGame?: string;
  lastSeen?: string;
}

export interface User {
  id: string;
  username: string;
  avatar: string;
  level: number;
  xp: number;
  xpToNext: number;
  gamesPlayed: number;
  friends: number;
  joinDate: string;
  bio: string;
  badges: Badge[];
}

export interface Badge {
  id: string;
  name: string;
  icon: string;
  description: string;
}

export interface ChatMessage {
  id: string;
  sender: string;
  content: string;
  timestamp: string;
}

export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  status: "uploading" | "converting" | "ready" | "error";
  progress: number;
  convertedGame?: Game;
}
