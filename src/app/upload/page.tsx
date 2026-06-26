"use client";

import { useState, useRef } from "react";
import { UploadedFile } from "@/lib/types";

export default function UploadPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const simulateUpload = (fileName: string, fileSize: number) => {
    const id = `upload-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const newFile: UploadedFile = {
      id,
      name: fileName,
      size: fileSize,
      status: "uploading",
      progress: 0,
    };

    setFiles((prev) => [newFile, ...prev]);

    // Simulate upload progress
    let progress = 0;
    const uploadInterval = setInterval(() => {
      progress += Math.random() * 15 + 5;
      if (progress >= 100) {
        progress = 100;
        clearInterval(uploadInterval);
        setFiles((prev) =>
          prev.map((f) => (f.id === id ? { ...f, status: "converting", progress: 100 } : f))
        );

        // Simulate conversion
        setTimeout(() => {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === id
                ? {
                    ...f,
                    status: "ready",
                    convertedGame: {
                      id: `converted-${id}`,
                      title: fileName.replace(/\.rblx$/i, "").replace(/[-_]/g, " "),
                      description: `Converted from ${fileName}`,
                      thumbnail: "build",
                      category: "Sandbox",
                      players: 0,
                      maxPlayers: 20,
                      rating: 0,
                      creator: "HNPP_Player",
                      tags: ["converted", "rblx"],
                    },
                  }
                : f
            )
          );
        }, 2000 + Math.random() * 2000);
      } else {
        setFiles((prev) =>
          prev.map((f) => (f.id === id ? { ...f, progress: Math.min(progress, 99) } : f))
        );
      }
    }, 200);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    droppedFiles.forEach((file) => {
      simulateUpload(file.name, file.size);
    });
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    selectedFiles.forEach((file) => {
      simulateUpload(file.name, file.size);
    });
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleDemoUpload = () => {
    const demoFiles = [
      { name: "my-obby-game.rblx", size: 4500000 },
      { name: "tycoon-adventure.rblx", size: 8200000 },
      { name: "racing-world.rblx", size: 6100000 },
    ];
    const demo = demoFiles[Math.floor(Math.random() * demoFiles.length)];
    simulateUpload(demo.name, demo.size);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const statusConfig = {
    uploading: { label: "Uploading", color: "text-blue-400", bg: "bg-blue-500" },
    converting: { label: "Converting to HNPP format", color: "text-yellow-400", bg: "bg-yellow-500" },
    ready: { label: "Ready to play!", color: "text-green-400", bg: "bg-green-500" },
    error: { label: "Error", color: "text-red-400", bg: "bg-red-500" },
  };

  return (
    <div className="p-4 lg:p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Upload RBLX Files</h1>
        <p className="text-gray-500 text-sm mt-1">
          Convert your Roblox game files (.rblx) to play on HNPP GAME
        </p>
      </div>

      {/* Upload Area */}
      <div
        className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 mb-8 ${
          isDragging
            ? "border-accent bg-accent/5 scale-[1.01]"
            : "border-dark-500 hover:border-primary hover:bg-dark-800/50"
        }`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        <div className="space-y-4">
          <div className={`w-20 h-20 mx-auto rounded-full flex items-center justify-center transition-colors ${isDragging ? "bg-accent/20" : "bg-dark-700"}`}>
            <svg className={`w-10 h-10 ${isDragging ? "text-accent" : "text-gray-500"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <div>
            <p className="text-lg font-semibold mb-1">
              {isDragging ? "Drop your files here!" : "Drag & drop your .rblx files here"}
            </p>
            <p className="text-sm text-gray-500">or click to browse</p>
          </div>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="btn-primary"
            >
              Browse Files
            </button>
            <button onClick={handleDemoUpload} className="btn-accent">
              Try Demo Upload
            </button>
          </div>
          <p className="text-xs text-gray-600">Supported: .rblx, .rbxl, .rbxlx (max 100MB)</p>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".rblx,.rbxl,.rbxlx"
          multiple
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {/* How it works */}
      <div className="bg-dark-800 rounded-xl p-6 border border-dark-600 mb-8">
        <h2 className="text-lg font-bold mb-4">How RBLX Conversion Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="w-14 h-14 mx-auto rounded-full bg-primary/20 flex items-center justify-center mb-3">
              <svg className="w-7 h-7 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
            </div>
            <h3 className="font-semibold text-sm mb-1">1. Upload</h3>
            <p className="text-xs text-gray-500">Upload your .rblx file from your computer</p>
          </div>
          <div className="text-center">
            <div className="w-14 h-14 mx-auto rounded-full bg-accent/20 flex items-center justify-center mb-3">
              <svg className="w-7 h-7 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
            <h3 className="font-semibold text-sm mb-1">2. Convert</h3>
            <p className="text-xs text-gray-500">We automatically convert it to HNPP format</p>
          </div>
          <div className="text-center">
            <div className="w-14 h-14 mx-auto rounded-full bg-warning/20 flex items-center justify-center mb-3">
              <svg className="w-7 h-7 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="font-semibold text-sm mb-1">3. Play</h3>
            <p className="text-xs text-gray-500">Play your converted game on HNPP GAME!</p>
          </div>
        </div>
      </div>

      {/* Uploaded Files */}
      {files.length > 0 && (
        <div>
          <h2 className="text-lg font-bold mb-4">Your Uploads</h2>
          <div className="space-y-3">
            {files.map((file) => {
              const config = statusConfig[file.status];
              return (
                <div key={file.id} className="bg-dark-800 rounded-xl p-4 border border-dark-600">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-lg bg-dark-700 flex items-center justify-center shrink-0">
                      <svg className="w-6 h-6 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <p className="font-medium text-sm truncate">{file.name}</p>
                        <span className={`text-xs font-medium ${config.color}`}>{config.label}</span>
                      </div>
                      <p className="text-xs text-gray-500 mb-2">{formatSize(file.size)}</p>
                      {file.status !== "ready" && (
                        <div className="w-full bg-dark-600 rounded-full h-1.5">
                          <div
                            className={`h-1.5 rounded-full ${config.bg} transition-all duration-300`}
                            style={{ width: `${file.progress}%` }}
                          />
                        </div>
                      )}
                    </div>
                    {file.status === "ready" && (
                      <button className="btn-accent text-sm py-1.5 px-4 shrink-0">
                        Play Now
                      </button>
                    )}
                  </div>
                  {file.status === "ready" && file.convertedGame && (
                    <div className="mt-3 pt-3 border-t border-dark-600 flex items-center gap-3">
                      <div className="w-8 h-8 rounded bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-xs font-bold">
                        {file.convertedGame.title[0]}
                      </div>
                      <div>
                        <p className="text-sm font-medium">{file.convertedGame.title}</p>
                        <p className="text-xs text-gray-500">Converted successfully - Ready to publish</p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
