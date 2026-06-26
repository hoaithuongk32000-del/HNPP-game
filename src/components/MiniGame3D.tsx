"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import * as THREE from "three";

interface MiniGame3DProps {
  gameType: string;
}

export default function MiniGame3D({ gameType }: MiniGame3DProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const playerRef = useRef<THREE.Mesh | null>(null);
  const animFrameRef = useRef<number>(0);
  const keysRef = useRef<Set<string>>(new Set());
  const [score, setScore] = useState(0);
  const [gameStarted, setGameStarted] = useState(false);
  const collectiblesRef = useRef<THREE.Mesh[]>([]);
  const obstaclesRef = useRef<THREE.Mesh[]>([]);
  const velocityRef = useRef({ x: 0, y: 0, z: 0 });
  const isGroundedRef = useRef(true);

  const initGame = useCallback(() => {
    if (!containerRef.current) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a2a);
    scene.fog = new THREE.Fog(0x0a0a2a, 30, 80);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(60, containerRef.current.clientWidth / containerRef.current.clientHeight, 0.1, 100);
    camera.position.set(0, 8, 12);
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    renderer.shadowMap.enabled = true;
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404080, 0.5);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 10, 5);
    directionalLight.castShadow = true;
    scene.add(directionalLight);

    const pointLight1 = new THREE.PointLight(0x6c5ce7, 1, 20);
    pointLight1.position.set(-5, 3, -5);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0x00cec9, 1, 20);
    pointLight2.position.set(5, 3, 5);
    scene.add(pointLight2);

    // Ground
    const groundGeo = new THREE.PlaneGeometry(60, 60);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x1a1a3e,
      roughness: 0.8,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    scene.add(ground);

    // Grid
    const gridHelper = new THREE.GridHelper(60, 30, 0x6c5ce7, 0x303066);
    gridHelper.position.y = 0.01;
    scene.add(gridHelper);

    // Player
    const playerGeo = new THREE.BoxGeometry(1, 1.5, 1);
    const playerMat = new THREE.MeshStandardMaterial({
      color: 0x6c5ce7,
      emissive: 0x6c5ce7,
      emissiveIntensity: 0.3,
    });
    const player = new THREE.Mesh(playerGeo, playerMat);
    player.position.y = 0.75;
    player.castShadow = true;
    scene.add(player);
    playerRef.current = player;

    // Player eyes
    const eyeGeo = new THREE.SphereGeometry(0.1, 8, 8);
    const eyeMat = new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 0.5 });
    const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
    leftEye.position.set(-0.2, 0.3, 0.5);
    player.add(leftEye);
    const rightEye = new THREE.Mesh(eyeGeo, eyeMat);
    rightEye.position.set(0.2, 0.3, 0.5);
    player.add(rightEye);

    // Platforms (obby style)
    const platformData = [
      { x: 0, y: 0, z: 0, w: 6, h: 0.5, d: 6, color: 0x1a1a3e },
      { x: 8, y: 1, z: 0, w: 4, h: 0.5, d: 4, color: 0x2a2a5e },
      { x: 8, y: 2, z: 8, w: 3, h: 0.5, d: 3, color: 0x3a3a7e },
      { x: 0, y: 3, z: 12, w: 5, h: 0.5, d: 3, color: 0x4a4a9e },
      { x: -8, y: 2, z: 8, w: 4, h: 0.5, d: 4, color: 0x2a2a5e },
      { x: -8, y: 4, z: 0, w: 3, h: 0.5, d: 3, color: 0x5a5abe },
      { x: -4, y: 5, z: -8, w: 4, h: 0.5, d: 4, color: 0x6c5ce7 },
      { x: 4, y: 3, z: -8, w: 3, h: 0.5, d: 5, color: 0x3a3a7e },
    ];

    platformData.forEach((p) => {
      const geo = new THREE.BoxGeometry(p.w, p.h, p.d);
      const mat = new THREE.MeshStandardMaterial({
        color: p.color,
        emissive: p.color,
        emissiveIntensity: 0.1,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(p.x, p.y, p.z);
      mesh.receiveShadow = true;
      scene.add(mesh);
      obstaclesRef.current.push(mesh);
    });

    // Collectibles (spinning gems)
    const gemPositions = [
      { x: 8, y: 2.5, z: 0 },
      { x: 8, y: 3.5, z: 8 },
      { x: 0, y: 4.5, z: 12 },
      { x: -8, y: 3.5, z: 8 },
      { x: -8, y: 5.5, z: 0 },
      { x: -4, y: 6.5, z: -8 },
      { x: 4, y: 4.5, z: -8 },
      { x: 2, y: 1.5, z: 2 },
      { x: -2, y: 1.5, z: -2 },
      { x: 0, y: 1.5, z: 0 },
    ];

    gemPositions.forEach((pos) => {
      const gemGeo = new THREE.OctahedronGeometry(0.3, 0);
      const gemMat = new THREE.MeshStandardMaterial({
        color: 0x00cec9,
        emissive: 0x00cec9,
        emissiveIntensity: 0.5,
        transparent: true,
        opacity: 0.9,
      });
      const gem = new THREE.Mesh(gemGeo, gemMat);
      gem.position.set(pos.x, pos.y, pos.z);
      gem.castShadow = true;
      scene.add(gem);
      collectiblesRef.current.push(gem);
    });

    // Decorative buildings
    for (let i = 0; i < 8; i++) {
      const h = 2 + Math.random() * 6;
      const buildingGeo = new THREE.BoxGeometry(2, h, 2);
      const buildingMat = new THREE.MeshStandardMaterial({
        color: 0x12122a,
        emissive: 0x6c5ce7,
        emissiveIntensity: 0.05,
      });
      const building = new THREE.Mesh(buildingGeo, buildingMat);
      const angle = (i / 8) * Math.PI * 2;
      building.position.set(Math.cos(angle) * 22, h / 2, Math.sin(angle) * 22);
      scene.add(building);
    }

    // Animation loop
    const clock = new THREE.Clock();
    const animate = () => {
      animFrameRef.current = requestAnimationFrame(animate);
      const delta = clock.getDelta();
      const speed = 8;
      const jumpForce = 10;
      const gravity = -25;

      if (playerRef.current) {
        const p = playerRef.current;

        // Movement
        if (keysRef.current.has("w") || keysRef.current.has("arrowup")) velocityRef.current.z = -speed;
        else if (keysRef.current.has("s") || keysRef.current.has("arrowdown")) velocityRef.current.z = speed;
        else velocityRef.current.z = 0;

        if (keysRef.current.has("a") || keysRef.current.has("arrowleft")) velocityRef.current.x = -speed;
        else if (keysRef.current.has("d") || keysRef.current.has("arrowright")) velocityRef.current.x = speed;
        else velocityRef.current.x = 0;

        // Jump
        if (keysRef.current.has(" ") && isGroundedRef.current) {
          velocityRef.current.y = jumpForce;
          isGroundedRef.current = false;
        }

        // Gravity
        velocityRef.current.y += gravity * delta;

        // Update position
        p.position.x += velocityRef.current.x * delta;
        p.position.y += velocityRef.current.y * delta;
        p.position.z += velocityRef.current.z * delta;

        // Ground collision
        if (p.position.y <= 0.75) {
          p.position.y = 0.75;
          velocityRef.current.y = 0;
          isGroundedRef.current = true;
        }

        // Platform collision
        obstaclesRef.current.forEach((platform) => {
          const pb = new THREE.Box3().setFromObject(platform);
          const playerBottom = p.position.y - 0.75;
          const playerTop = p.position.y + 0.75;

          if (
            p.position.x > pb.min.x - 0.5 &&
            p.position.x < pb.max.x + 0.5 &&
            p.position.z > pb.min.z - 0.5 &&
            p.position.z < pb.max.z + 0.5
          ) {
            if (playerBottom <= pb.max.y && playerBottom >= pb.max.y - 0.5 && velocityRef.current.y <= 0) {
              p.position.y = pb.max.y + 0.75;
              velocityRef.current.y = 0;
              isGroundedRef.current = true;
            } else if (playerTop >= pb.min.y && playerTop <= pb.min.y + 0.5 && velocityRef.current.y > 0) {
              velocityRef.current.y = 0;
            }
          }
        });

        // Boundary
        p.position.x = Math.max(-25, Math.min(25, p.position.x));
        p.position.z = Math.max(-25, Math.min(25, p.position.z));

        // Fall reset
        if (p.position.y < -10) {
          p.position.set(0, 2, 0);
          velocityRef.current = { x: 0, y: 0, z: 0 };
          isGroundedRef.current = true;
        }

        // Camera follow
        camera.position.x = p.position.x;
        camera.position.y = p.position.y + 8;
        camera.position.z = p.position.z + 12;
        camera.lookAt(p.position);

        // Collectible collision
        collectiblesRef.current = collectiblesRef.current.filter((gem) => {
          const dist = p.position.distanceTo(gem.position);
          if (dist < 1.2) {
            scene.remove(gem);
            setScore((prev) => prev + 100);
            return false;
          }
          return true;
        });
      }

      // Animate collectibles
      collectiblesRef.current.forEach((gem, i) => {
        gem.rotation.y += delta * 2;
        gem.position.y += Math.sin(Date.now() * 0.003 + i) * 0.003;
      });

      renderer.render(scene, camera);
    };

    animate();

    // Resize handler
    const handleResize = () => {
      if (!containerRef.current) return;
      camera.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  useEffect(() => {
    if (!gameStarted) return;

    const container = containerRef.current;
    const cleanup = initGame();

    const handleKeyDown = (e: KeyboardEvent) => {
      keysRef.current.add(e.key.toLowerCase());
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      keysRef.current.delete(e.key.toLowerCase());
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
      cancelAnimationFrame(animFrameRef.current);
      if (rendererRef.current && container) {
        container.removeChild(rendererRef.current.domElement);
        rendererRef.current.dispose();
      }
      collectiblesRef.current = [];
      obstaclesRef.current = [];
      if (cleanup) cleanup();
    };
  }, [gameStarted, initGame]);

  if (!gameStarted) {
    return (
      <div className="w-full h-full bg-dark-800 rounded-xl flex flex-col items-center justify-center gap-6">
        <div className="text-center">
          <h2 className="text-3xl font-bold neon-text mb-2">{gameType}</h2>
          <p className="text-gray-400">Collect gems and explore the world!</p>
        </div>
        <div className="bg-dark-700 rounded-lg p-4 text-sm text-gray-300">
          <p className="font-semibold text-accent mb-2">Controls:</p>
          <p>WASD / Arrow Keys - Move</p>
          <p>Space - Jump</p>
          <p>Collect glowing gems for points!</p>
        </div>
        <button
          onClick={() => setGameStarted(true)}
          className="btn-primary text-lg px-10 py-3 animate-pulse-glow"
        >
          PLAY NOW
        </button>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full rounded-xl overflow-hidden" />
      {/* HUD */}
      <div className="absolute top-4 left-4 glass rounded-lg px-4 py-2">
        <div className="flex items-center gap-2">
          <span className="text-accent font-bold text-lg">{score}</span>
          <span className="text-xs text-gray-400">SCORE</span>
        </div>
      </div>
      <div className="absolute top-4 right-4 glass rounded-lg px-4 py-2">
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span>WASD/Arrows: Move</span>
          <span>|</span>
          <span>Space: Jump</span>
        </div>
      </div>
      {collectiblesRef.current.length === 0 && score > 0 && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/60">
          <div className="text-center">
            <h2 className="text-4xl font-bold neon-text-accent mb-4">YOU WIN!</h2>
            <p className="text-2xl text-white mb-2">Score: {score}</p>
            <button
              onClick={() => {
                setScore(0);
                setGameStarted(false);
              }}
              className="btn-primary mt-4"
            >
              Play Again
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
