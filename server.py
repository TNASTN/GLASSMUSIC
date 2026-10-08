import os
import re
import struct
import requests
import zlib
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response, StreamingResponse

app = FastAPI(title="Glassmorphism Audio Streamer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover, maximum-scale=1.0, user-scalable=no">
  <meta name="theme-color" content="#272044">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="Glass Audio">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="manifest" href="/manifest.json">
  <link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
  <title>Glass Audio</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    /* Thanh cuộn mảnh & hiệu ứng kính */
    .glass-panel {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.15);
    }
    .glass-card {
      background: rgba(255, 255, 255, 0.03);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.1);
    }
    .glass-btn {
      background: rgba(255, 255, 255, 0.08);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.15);
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    .glass-btn:active {
      transform: scale(0.95);
      background: rgba(255, 255, 255, 0.15);
    }
    /* Thanh gạt Range kiểu iOS */
    input[type=range] {
      accent-color: #ec4899;
    }
    .vertical-slider {
      writing-mode: vertical-lr;
      direction: rtl;
      appearance: none;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 9999px;
      outline: none;
    }
    .vertical-slider::-webkit-slider-thumb {
      appearance: none;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: #ec4899;
      cursor: pointer;
      box-shadow: 0 0 10px rgba(236, 72, 153, 0.8);
    }
    body {
      min-height: 100vh;
      min-height: 100svh;
      overscroll-behavior: none;
      -webkit-tap-highlight-color: transparent;
      background:
        radial-gradient(ellipse at 20% 8%, rgba(147, 119, 230, 0.55), transparent 38%),
        radial-gradient(ellipse at 92% 46%, rgba(255, 136, 177, 0.4), transparent 34%),
        radial-gradient(ellipse at 10% 82%, rgba(79, 73, 164, 0.45), transparent 36%),
        linear-gradient(155deg, #272044 0%, #29213e 43%, #101326 100%);
      background-attachment: fixed;
    }
    .player-shell {
      width: min(100%, 370px);
      min-height: min(790px, calc(100svh - 24px));
      max-height: calc(100svh - 24px);
      box-sizing: border-box;
      overflow-y: auto;
      border-radius: 32px;
      padding: max(clamp(14px, 3vh, 22px), env(safe-area-inset-top)) max(clamp(16px, 6vw, 24px), env(safe-area-inset-right)) max(20px, env(safe-area-inset-bottom)) max(clamp(16px, 6vw, 24px), env(safe-area-inset-left));
      gap: 0;
      -webkit-overflow-scrolling: touch;
      overscroll-behavior: contain;
      border-color: rgba(255, 255, 255, 0.34);
      background: linear-gradient(155deg, rgba(230, 218, 255, 0.22), rgba(170, 158, 219, 0.11) 45%, rgba(20, 20, 48, 0.48));
      box-shadow: 0 24px 75px rgba(9, 8, 27, 0.48), inset 0 1px 1px rgba(255, 255, 255, 0.28);
    }
    .player-header {
      min-height: 40px;
      margin-bottom: 14px;
      color: rgba(255, 255, 255, 0.86);
    }
    .player-header button {
      width: 32px;
      height: 32px;
      display: grid;
      place-items: center;
      color: rgba(255, 255, 255, 0.88);
    }
    .player-header-title {
      font-size: 13px;
      font-weight: 500;
      letter-spacing: 0.02em;
    }
    #urlForm {
      margin-bottom: 14px;
      padding: 12px;
      border: 1px solid rgba(255, 255, 255, 0.18);
      border-radius: 18px;
      background: rgba(25, 22, 54, 0.42);
    }
    #urlForm input {
      min-height: 42px;
      font-size: 12px;
    }
    #btnSubmit {
      min-height: 42px;
    }
    #playerBox {
      gap: 0;
    }
    .album-art {
      width: min(100%, 300px, 38svh, 76vw);
      height: auto;
      aspect-ratio: 1;
      border-radius: 21px;
      padding: 0;
      margin-bottom: 23px;
      box-shadow: 0 18px 38px rgba(12, 10, 33, 0.42);
    }
    .album-art img {
      border-radius: 20px;
    }
    .track-info {
      margin-bottom: 18px;
    }
    .track-info h2 {
      font-size: 17px;
      line-height: 1.35;
    }
    .track-info p {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.68);
    }
    .progress-area {
      margin-bottom: 9px;
    }
    input[type=range].seek-control {
      height: 3px;
      accent-color: #fff;
    }
    .transport-controls {
      justify-content: space-between;
      gap: 10px;
      padding: 5px 0 19px;
    }
    .transport-controls button {
      flex: 0 0 auto;
    }
    .transport-btn {
      width: 34px;
      height: 38px;
      display: grid;
      place-items: center;
      color: rgba(255, 255, 255, 0.9);
      font-size: 17px;
    }
    .transport-btn.subtle {
      color: rgba(255, 255, 255, 0.62);
      font-size: 14px;
    }
    #btnPlayPause {
      width: 64px;
      height: 64px;
      background: rgba(255, 255, 255, 0.08);
      -webkit-backdrop-filter: blur(14px);
      backdrop-filter: blur(14px);
      box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.18);
      border-color: rgba(255, 255, 255, 0.42);
    }
    #btnPlayPause:hover {
      background: rgba(255, 255, 255, 0.14);
    }
    #btnPlayPause:active {
      background: rgba(255, 255, 255, 0.2);
    }
    #playIcon {
      display: grid;
      place-items: center;
      width: 22px;
      height: 22px;
      color: #fff;
    }
    #playIcon svg {
      display: block;
      width: 100%;
      height: 100%;
    }
    .utility-bar {
      display: flex;
      justify-content: space-around;
      align-items: center;
      min-height: 44px;
      border-radius: 999px;
      border: 1px solid rgba(255, 255, 255, 0.19);
      background: rgba(219, 210, 255, 0.14);
      box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.18);
    }
    .utility-bar button,
    .utility-bar a {
      flex: 1;
      width: auto;
      min-width: 0;
      height: 40px;
      display: grid;
      place-items: center;
      color: rgba(255, 255, 255, 0.78);
      border-radius: 999px;
    }
    .utility-bar button:hover,
    .utility-bar a:hover {
      background: rgba(255, 255, 255, 0.12);
      color: #fff;
    }
    .library-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      max-height: 30vh;
      overflow-y: auto;
    }
    .library-row {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.05);
    }
    .library-row-play {
      flex: 1;
      min-width: 0;
      text-align: left;
    }
    .library-row-play strong,
    .library-row-play span {
      display: block;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .library-row-play strong {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.94);
    }
    .library-row-play span {
      margin-top: 2px;
      font-size: 10px;
      color: rgba(255, 255, 255, 0.58);
    }
    .library-row-remove {
      width: 32px;
      height: 32px;
      flex: 0 0 32px;
      border-radius: 50%;
      color: rgba(255, 255, 255, 0.65);
    }
    .library-row-remove:hover {
      background: rgba(255, 255, 255, 0.1);
      color: #fff;
    }
    .sleep-select {
      color: white;
      background: rgba(255, 255, 255, 0.08);
    }
    .sleep-select option {
      color: #171326;
    }
    #sleepStatus {
      min-height: 18px;
    }
    .volume-area {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-top: 17px;
      color: rgba(255, 255, 255, 0.78);
    }
    .volume-area input {
      height: 3px;
      accent-color: #fff;
    }
    .eq-preset {
      color: #f4efff;
      background-color: rgba(255, 255, 255, 0.08);
    }
    .eq-preset:focus {
      outline: 2px solid rgba(216, 180, 254, 0.75);
      outline-offset: 2px;
    }
    @media (max-height: 740px) {
      .player-shell {
        min-height: 0;
        padding-top: 12px;
        padding-bottom: 12px;
      }
      .album-art {
        width: min(100%, 250px, 34svh, 76vw);
        margin-bottom: clamp(10px, 2vh, 16px);
      }
      .track-info {
        margin-bottom: clamp(8px, 1.8vh, 12px);
      }
      .transport-controls {
        padding-bottom: clamp(8px, 1.8vh, 12px);
      }
      #btnPlayPause {
        width: clamp(48px, 9vh, 64px);
        height: clamp(48px, 9vh, 64px);
      }
      .player-header {
        min-height: 34px;
        margin-bottom: 8px;
      }
      .volume-area {
        margin-top: 10px;
      }
    }
    @media (max-width: 360px) {
      .player-shell {
        width: 100%;
        border-radius: 26px;
      }
      .transport-controls {
        gap: 4px;
      }
      .transport-btn {
        width: 30px;
      }
    }
    @media (max-height: 560px) {
      .player-shell {
        padding-top: 8px;
        padding-bottom: 8px;
      }
      .album-art {
        width: min(100%, 180px, 28svh, 60vw);
        margin-bottom: 8px;
      }
      .track-info {
        margin-bottom: 6px;
      }
      .progress-area {
        margin-bottom: 4px;
      }
      .transport-controls {
        padding-top: 2px;
        padding-bottom: 6px;
      }
      .utility-bar {
        min-height: 38px;
      }
      .utility-bar button,
      .utility-bar a {
        height: 34px;
      }
      .volume-area {
        margin-top: 6px;
      }
    }
  </style>
</head>
<body class="text-zinc-100 min-h-screen flex items-center justify-center p-3 select-none relative overflow-x-hidden font-sans">
  
  <!-- Các vòm sáng nền tạo hiệu ứng bóng gương -->
  <div class="fixed -top-32 -left-32 w-80 h-80 bg-pink-500/20 rounded-full blur-[100px] pointer-events-none"></div>
  <div class="fixed -bottom-32 -right-32 w-80 h-80 bg-violet-600/20 rounded-full blur-[100px] pointer-events-none"></div>

  <!-- Khung máy chính -->
  <div class="player-shell glass-panel flex flex-col relative z-10">
    
    <!-- Header -->
    <div class="player-header flex items-center justify-between">
      <button id="btnToggleForm" type="button" aria-label="Mở mục thêm nhạc" title="Thêm nhạc">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m6 9 6 6 6-6"/></svg>
      </button>
      <span class="player-header-title">Đang phát</span>
      <button id="btnToggleFormMenu" type="button" aria-label="Thêm bài hát" title="Thêm bài hát" class="text-xl tracking-widest">···</button>
    </div>

    <!-- Ô dán link YouTube -->
    <form id="urlForm" class="hidden space-y-2">
      <div class="relative">
        <input 
          type="url" 
          id="videoUrl" 
          placeholder="Dán liên kết video tại đây..." 
          required 
          class="w-full px-4 py-3 rounded-2xl glass-card text-xs focus:outline-none focus:border-pink-400/50 text-white placeholder-zinc-500 transition"
        >
      </div>
      <button 
        type="submit" 
        id="btnSubmit" 
        class="w-full py-3 bg-gradient-to-r from-pink-500/80 to-violet-600/80 hover:from-pink-500 hover:to-violet-600 active:scale-[0.98] font-semibold rounded-2xl text-xs transition duration-200 shadow-[0_8px_20px_rgba(236,72,153,0.3)] border border-white/20 flex items-center justify-center gap-2"
      >
        <span>Tách Luồng & Phát Âm Thanh</span>
      </button>
    </form>

    <!-- Trạng thái tải -->
    <div id="loader" class="text-center text-xs text-pink-200 hidden animate-pulse py-2">
      Đang giải mã và kết nối luồng phát chất lượng cao...
    </div>

    <!-- Khung phát âm thanh gương -->
    <div id="playerBox" class="hidden flex flex-col pt-1">
      
      <!-- Ảnh bìa gương lớn bo cong -->
      <div class="album-art relative group mx-auto rounded-[28px] overflow-hidden glass-card">
        <img id="thumb" class="w-full h-full rounded-[24px] object-cover bg-zinc-800" src="" alt="Thumbnail">
        <div class="absolute inset-0 rounded-[28px] border border-white/20 pointer-events-none"></div>
      </div>

      <!-- Tên bài hát & Kênh -->
      <div class="track-info text-center px-3 space-y-0.5">
        <h2 id="songTitle" class="font-bold text-sm truncate text-white drop-shadow">Đang tải tên bài hát...</h2>
        <p id="songArtist" class="text-xs text-zinc-400 truncate">Kênh nghệ sĩ</p>
      </div>

      <!-- Thẻ audio ẩn điều khiển bằng API -->
      <audio id="audioEl" crossorigin="anonymous" playsinline preload="metadata"></audio>

      <!-- Thanh tua bài (Seek Bar) -->
      <div class="progress-area space-y-1 px-1">
        <input 
          type="range" 
          id="seekBar" 
          min="0" 
          max="100" 
          value="0" 
          step="0.1" 
          class="seek-control w-full h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer accent-pink-500"
        >
        <div class="flex justify-between text-[10px] text-zinc-400 font-mono">
          <span id="currentTime">00:00</span>
          <span id="durationTime">00:00</span>
        </div>
      </div>

      <!-- Điều khiển phát -->
      <div class="transport-controls flex items-center">
        <button id="btnShuffle" class="transport-btn subtle" type="button" aria-label="Phát ngẫu nhiên" title="Phát ngẫu nhiên">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="m18 14 4 4-4 4m0-20 4 4-4 4M2 18h2.5a6 6 0 0 0 4.2-1.7L17.5 7.5A6 6 0 0 1 21.7 6H22M2 6h2.5a6 6 0 0 1 4.2 1.7l1.2 1.2M14.5 14.5l3 3A6 6 0 0 0 21.7 19H22"/></svg>
        </button>
        <button id="btnBackward" class="transport-btn" aria-label="Lùi 15 giây" title="Lùi 15 giây">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M6 5h2v14H6zM20 5v14L9 12z"/></svg>
        </button>
        <button id="btnPlayPause" type="button" aria-label="Phát nhạc" title="Phát nhạc" class="rounded-full flex items-center justify-center text-white active:scale-95 transition border">
          <span id="playIcon" aria-hidden="true"></span>
        </button>
        <button id="btnForward" class="transport-btn" aria-label="Tua tới 15 giây" title="Tua tới 15 giây">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M16 5h2v14h-2zM4 5v14l11-7z"/></svg>
        </button>
        <button id="btnRepeat" class="transport-btn subtle" type="button" aria-label="Lặp lại" title="Lặp lại">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="m17 2 4 4-4 4M3 11V9a3 3 0 0 1 3-3h15M7 22l-4-4 4-4m14-1v2a3 3 0 0 1-3 3H3"/></svg>
        </button>
      </div>

      <div class="utility-bar">
        <button id="btnOpenSpeed" type="button" aria-label="Tốc độ phát" title="Tốc độ phát">
          <span id="currentSpeedLabel" class="text-xs font-bold">1.0x</span>
        </button>
        <button id="btnOpenEQ" type="button" aria-label="Bộ cân bằng âm sắc" title="Bộ cân bằng âm sắc">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M4 18v-5m0-4V6m5 14v-9m0-4V4m5 16v-7m0-4V4m5 16v-5m0-4V4M2 13h4m1-6h4m1 7h4m1-5h4"/></svg>
        </button>
        <button id="btnOpenLibrary" type="button" aria-label="Danh sách phát và lịch sử" title="Danh sách phát và lịch sử">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01"/></svg>
        </button>
        <button id="btnOpenSleep" type="button" aria-label="Hẹn giờ tự dừng" title="Hẹn giờ tự dừng">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="13" r="8" stroke-width="1.8"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 9v4l2.5 1.5M9 2h6M19 5l1.5-1.5"/></svg>
        </button>
        <a id="btnDownload" href="#" download aria-label="Tải bài hát" title="Tải bài hát">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 3v12m0 0 4-4m-4 4-4-4m-4 7h16"/></svg>
        </a>
        <button id="btnSettings" type="button" aria-label="Mở mục thêm nhạc" title="Thêm nhạc">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3" stroke-width="1.8"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="m19.4 15 .1.1a1.8 1.8 0 1 1-2.5 2.5l-.1-.1a1.8 1.8 0 0 0-3 .9v.2a1.8 1.8 0 1 1-3.6 0v-.2a1.8 1.8 0 0 0-3-.9l-.1.1a1.8 1.8 0 1 1-2.5-2.5l.1-.1a1.8 1.8 0 0 0-.9-3h-.2a1.8 1.8 0 1 1 0-3.6h.2a1.8 1.8 0 0 0 .9-3l-.1-.1a1.8 1.8 0 1 1 2.5-2.5l.1.1a1.8 1.8 0 0 0 3-.9v-.2a1.8 1.8 0 1 1 3.6 0v.2a1.8 1.8 0 0 0 3 .9l.1-.1a1.8 1.8 0 1 1 2.5 2.5l-.1.1a1.8 1.8 0 0 0 .9 3h.2a1.8 1.8 0 1 1 0 3.6h-.2a1.8 1.8 0 0 0-.9 3Z"/></svg>
        </button>
      </div>

      <div class="volume-area">
        <svg class="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 9v6h4l5 4V5L7 9H3zm13.5 3a4.5 4.5 0 0 0-2.5-4.03v8.05a4.5 4.5 0 0 0 2.5-4.02zM14 3.23v2.06a7 7 0 0 1 0 13.42v2.06a9 9 0 0 0 0-17.54z"/></svg>
        <input id="volumeBar" type="range" min="0" max="1" step="0.01" value="0.8" class="w-full cursor-pointer" aria-label="Âm lượng">
        <svg class="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 9v6h4l5 4V5L7 9H3zm13.5 3a4.5 4.5 0 0 0-2.5-4.03v8.05a4.5 4.5 0 0 0 2.5-4.02zM14 3.23v2.06a7 7 0 0 1 0 13.42v2.06a9 9 0 0 0 0-17.54z"/></svg>
      </div>
    </div>
  </div>

  <!-- POP-UP 1: BẢNG CHỌN TỐC ĐỘ (SPEED MODAL) -->
  <div id="speedModal" class="fixed inset-0 bg-black/60 backdrop-blur-md hidden items-center justify-center p-4 z-50 transition-opacity">
    <div class="glass-panel w-full max-w-[320px] rounded-3xl p-5 space-y-4 border border-white/20">
      <div class="flex justify-between items-center">
        <h3 class="text-xs font-bold uppercase tracking-wider text-pink-400">Chọn Tốc Độ Phát</h3>
        <button id="btnCloseSpeed" class="glass-btn w-7 h-7 rounded-full text-xs flex items-center justify-center text-zinc-400 hover:text-white">✕</button>
      </div>
      <div class="grid grid-cols-3 gap-2">
        <button class="speed-opt glass-btn py-3 rounded-2xl text-xs font-semibold" data-speed="0.5">0.5x</button>
        <button class="speed-opt glass-btn py-3 rounded-2xl text-xs font-semibold" data-speed="0.75">0.75x</button>
        <button class="speed-opt glass-btn py-3 rounded-2xl text-xs font-semibold bg-pink-500/40 border-pink-400/50 text-white" data-speed="1.0">1.0x</button>
        <button class="speed-opt glass-btn py-3 rounded-2xl text-xs font-semibold" data-speed="1.25">1.25x</button>
        <button class="speed-opt glass-btn py-3 rounded-2xl text-xs font-semibold" data-speed="1.5">1.5x</button>
        <button class="speed-opt glass-btn py-3 rounded-2xl text-xs font-semibold" data-speed="2.0">2.0x</button>
      </div>
    </div>
  </div>

  <!-- POP-UP 2: BẢNG ĐIỀU KHIỂN EQ ĐA DẢI TẦN (7-BAND EQUALIZER MODAL) -->
  <div id="eqModal" class="fixed inset-0 bg-black/70 backdrop-blur-lg hidden items-center justify-center p-3 z-50 transition-opacity">
    <div class="glass-panel w-full max-w-[380px] rounded-3xl p-5 space-y-4 border border-white/20 max-h-[92vh] overflow-y-auto">
      
      <div class="flex justify-between items-center border-b border-white/10 pb-3">
        <div>
          <h3 class="text-sm font-bold text-violet-400 flex items-center gap-1.5">
            <span>🎚️</span> Bộ Cân Bằng Âm Sắc (EQ)
          </h3>
          <p class="text-[10px] text-zinc-400 mt-0.5">Tăng/giảm từng nấc 1dB (-12dB đến +12dB)</p>
        </div>

        <div id="libraryModal" class="fixed inset-0 bg-black/70 backdrop-blur-lg hidden items-center justify-center p-3 z-50">
          <div class="glass-panel w-full max-w-[380px] rounded-3xl p-5 space-y-4 border border-white/20 max-h-[90vh] overflow-y-auto">
            <div class="flex justify-between items-center border-b border-white/10 pb-3">
              <div>
                <h3 class="text-sm font-bold text-violet-300">Thư viện nhạc</h3>
                <p class="text-[10px] text-zinc-400 mt-1">Danh sách và lịch sử được lưu trên thiết bị này</p>
              </div>
              <button id="btnCloseLibrary" type="button" class="glass-btn w-8 h-8 rounded-full text-xs text-zinc-300">✕</button>
            </div>
            <p id="libraryStatus" class="text-[11px] text-rose-300" role="status" aria-live="polite"></p>
            <button id="btnSaveCurrent" type="button" class="w-full glass-btn rounded-xl py-2.5 text-xs text-white">＋ Lưu bài đang phát vào danh sách</button>
            <section class="space-y-2">
              <div class="flex items-center justify-between">
                <h4 class="text-xs font-semibold text-white">Danh sách phát</h4>
                <span id="playlistCount" class="text-[10px] text-zinc-400">0 bài</span>
              </div>
              <div id="playlistItems" class="library-list"></div>
              <p id="playlistEmpty" class="text-[10px] text-zinc-500">Chưa có bài nào được lưu.</p>
            </section>
            <section class="space-y-2 border-t border-white/10 pt-3">
              <div class="flex items-center justify-between">
                <h4 class="text-xs font-semibold text-white">Đã nghe gần đây</h4>
                <button id="btnClearHistory" type="button" class="text-[10px] text-zinc-400 hover:text-white">Xóa lịch sử</button>
              </div>
              <div id="historyItems" class="library-list"></div>
              <p id="historyEmpty" class="text-[10px] text-zinc-500">Lịch sử nghe sẽ xuất hiện tại đây.</p>
            </section>
          </div>
        </div>

        <div id="sleepModal" class="fixed inset-0 bg-black/70 backdrop-blur-lg hidden items-center justify-center p-3 z-50">
          <div class="glass-panel w-full max-w-[320px] rounded-3xl p-5 space-y-4 border border-white/20">
            <div class="flex justify-between items-center">
              <h3 class="text-sm font-bold text-violet-300">Hẹn giờ tự dừng</h3>
              <button id="btnCloseSleep" type="button" class="glass-btn w-8 h-8 rounded-full text-xs text-zinc-300">✕</button>
            </div>
            <label class="block space-y-2">
              <span class="text-[10px] text-zinc-400">Dừng phát sau</span>
              <select id="sleepDuration" class="sleep-select w-full rounded-xl border border-white/15 px-3 py-3 text-xs">
                <option value="5">5 phút</option>
                <option value="10">10 phút</option>
                <option value="15" selected>15 phút</option>
                <option value="30">30 phút</option>
                <option value="45">45 phút</option>
                <option value="60">60 phút</option>
              </select>
            </label>
            <p id="sleepStatus" class="text-[11px] text-zinc-300" role="status" aria-live="polite">Chưa bật hẹn giờ.</p>
            <div class="grid grid-cols-2 gap-2">
              <button id="btnStartSleep" type="button" class="glass-btn rounded-xl py-3 text-xs font-semibold text-white">Bắt đầu</button>
              <button id="btnCancelSleep" type="button" class="glass-btn rounded-xl py-3 text-xs text-zinc-300">Hủy hẹn giờ</button>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button id="btnResetEQ" class="text-[10px] bg-white/5 hover:bg-white/10 border border-white/10 px-2.5 py-1 rounded-full text-zinc-300">0dB</button>
          <button id="btnCloseEQ" class="glass-btn w-7 h-7 rounded-full text-xs flex items-center justify-center text-zinc-400 hover:text-white">✕</button>
        </div>
      </div>

      <label class="block space-y-2">
        <span class="text-[10px] uppercase tracking-wider text-zinc-400">Kiểu nhạc</span>
        <select id="eqPreset" class="eq-preset w-full rounded-xl border border-white/15 px-3 py-2.5 text-xs">
          <option value="flat">Bình thường</option>
          <option value="pop">Pop</option>
          <option value="rock">Rock</option>
          <option value="jazz">Jazz</option>
          <option value="classical">Cổ điển</option>
          <option value="edm">EDM</option>
          <option value="acoustic">Acoustic</option>
          <option value="hiphop">Hip-hop</option>
          <option value="custom">Tùy chỉnh</option>
        </select>
      </label>

      <!-- 7 Cột Tần Số (60Hz, 150Hz, 400Hz, 1kHz, 2.5kHz, 6kHz, 14kHz) -->
      <div class="grid grid-cols-7 gap-1.5 pt-2 text-center">
        
        <!-- Helper Function tạo 7 band trong JS hoặc render tĩnh -->
        <!-- Band 0: 60Hz -->
        <div class="flex flex-col items-center space-y-1.5 eq-column" data-band="0">
          <span class="text-[9px] text-zinc-400 font-mono">60Hz</span>
          <button class="btn-step-plus glass-btn w-6 h-6 rounded-full text-[11px] font-bold text-pink-400 flex items-center justify-center">+</button>
          <input type="range" class="vertical-slider w-3 h-28 my-1" min="-12" max="12" value="0" step="1">
          <button class="btn-step-minus glass-btn w-6 h-6 rounded-full text-[11px] font-bold text-zinc-400 flex items-center justify-center">-</button>
          <span class="text-[9px] font-mono text-zinc-300 eq-db-label">0dB</span>
        </div>

        <!-- Band 1: 150Hz -->
        <div class="flex flex-col items-center space-y-1.5 eq-column" data-band="1">
          <span class="text-[9px] text-zinc-400 font-mono">150Hz</span>
          <button class="btn-step-plus glass-btn w-6 h-6 rounded-full text-[11px] font-bold text-pink-400 flex items-center justify-center">+</button>
          <input type="range" class="vertical-slider w-3 h-28 my-1" min="-12" max="12" value="0" step="1">
          <button class="btn-step-minus glass-btn w-6 h-6 rounded-full text-[11px] font-bold text-zinc-400 flex items-center justify-center">-</button>
          <span class="text-[9px] font-mono text-zinc-300 eq-db-label">0dB</span>
        </div>

        <!-- Band 2: 400Hz -->
        <div class="flex flex-col items-center space-y-1.5 eq-column" data-band="2">
          <span class="text-[9px] text-zinc-400 font-mono">400Hz</span>
          <button class="btn-step-plus glass-btn w-6 h-6 rounded-full text-[11px] font-bold text-pink-400 flex items-center justify-center">+</button>
          <input type="range" class="vertical-slider w-3 h-28 my-1" min="-12" max="12" value="0" step="1">
          <button class="btn-step-minus glass-btn w-6 h-6 rounded-full text-[11px] font-bold text-zinc-400 flex items-center justify-center">-</button>
          <span class="text-[9px] font-mono text-zinc-300 eq-db-label">0dB</span>
        </div>

        <!-- Band 3: 1kHz -->
        <div class="flex flex-col items-center space-y-1.5 eq-column" data-band="3">
          <span class="text-[9px] text-zinc-400 font-mono">1kHz</span>
          <button class="btn-step-plus glass-btn w-6 h-6 rounded-full text-[11px] font-bold text-pink-400 flex items-center justify-center">+</button>
          <input type="range" class="vertical-slider w-3 h-28 my-1" min="-12" max="12" value="0" step="1">
          <button class="btn-step-minus glass-btn w-6 h-6 rounded-full text-[11px] font-bold text-zinc-400 flex items-center justify-center">-</button>
          <span class="text-[9px] font-mono text-zinc-300 eq-db-label">0dB</span>
        </div>

        <!-- Band 4: 2.5kHz -->
        <div class="flex flex-col items-center space-y-1.5 eq-column" data-band="4">
          <span class="text-[9px] text-zinc-400 font-mono">2.5k</span>
          <button class="btn-step-plus glass-btn w-6 h-6 rounded-full text-[11px] font-bold text-pink-400 flex items-center justify-center">+</button>
          <input type="range" class="vertical-slider w-3 h-28 my-1" min="-12" max="12" value="0" step="1">
          <button class="btn-step-minus glass-btn w-6 h-6 rounded-full text-[11px] font-bold text-zinc-400 flex items-center justify-center">-</button>
          <span class="text-[9px] font-mono text-zinc-300 eq-db-label">0dB</span>
        </div>

        <!-- Band 5: 6kHz -->
        <div class="flex flex-col items-center space-y-1.5 eq-column" data-band="5">
          <span class="text-[9px] text-zinc-400 font-mono">6kHz</span>
          <button class="btn-step-plus glass-btn w-6 h-6 rounded-full text-[11px] font-bold text-pink-400 flex items-center justify-center">+</button>
          <input type="range" class="vertical-slider w-3 h-28 my-1" min="-12" max="12" value="0" step="1">
          <button class="btn-step-minus glass-btn w-6 h-6 rounded-full text-[11px] font-bold text-zinc-400 flex items-center justify-center">-</button>
          <span class="text-[9px] font-mono text-zinc-300 eq-db-label">0dB</span>
        </div>

        <!-- Band 6: 14kHz -->
        <div class="flex flex-col items-center space-y-1.5 eq-column" data-band="6">
          <span class="text-[9px] text-zinc-400 font-mono">14k</span>
          <button class="btn-step-plus glass-btn w-6 h-6 rounded-full text-[11px] font-bold text-pink-400 flex items-center justify-center">+</button>
          <input type="range" class="vertical-slider w-3 h-28 my-1" min="-12" max="12" value="0" step="1">
          <button class="btn-step-minus glass-btn w-6 h-6 rounded-full text-[11px] font-bold text-zinc-400 flex items-center justify-center">-</button>
          <span class="text-[9px] font-mono text-zinc-300 eq-db-label">0dB</span>
        </div>

      </div>

    </div>
  </div>

  <script>
    const form = document.getElementById('urlForm');
    const input = document.getElementById('videoUrl');
    const loader = document.getElementById('loader');
    const playerBox = document.getElementById('playerBox');
    const audio = document.getElementById('audioEl');
    const thumb = document.getElementById('thumb');
    const songTitle = document.getElementById('songTitle');
    const songArtist = document.getElementById('songArtist');
    const btnSubmit = document.getElementById('btnSubmit');
    const btnDownload = document.getElementById('btnDownload');

    const seekBar = document.getElementById('seekBar');
    const currentTimeEl = document.getElementById('currentTime');
    const durationTimeEl = document.getElementById('durationTime');
    const btnPlayPause = document.getElementById('btnPlayPause');
    const playIcon = document.getElementById('playIcon');
    const btnBackward = document.getElementById('btnBackward');
    const btnForward = document.getElementById('btnForward');
    const volumeBar = document.getElementById('volumeBar');
    const btnToggleForm = document.getElementById('btnToggleForm');
    const btnToggleFormMenu = document.getElementById('btnToggleFormMenu');
    const btnSettings = document.getElementById('btnSettings');
    const btnOpenLibrary = document.getElementById('btnOpenLibrary');
    const btnOpenSleep = document.getElementById('btnOpenSleep');
    const eqPreset = document.getElementById('eqPreset');
    const btnRepeat = document.getElementById('btnRepeat');

    // Modals
    const speedModal = document.getElementById('speedModal');
    const btnOpenSpeed = document.getElementById('btnOpenSpeed');
    const btnCloseSpeed = document.getElementById('btnCloseSpeed');
    const currentSpeedLabel = document.getElementById('currentSpeedLabel');

    const eqModal = document.getElementById('eqModal');
    const btnOpenEQ = document.getElementById('btnOpenEQ');
    const btnCloseEQ = document.getElementById('btnCloseEQ');
    const btnResetEQ = document.getElementById('btnResetEQ');
    const libraryModal = document.getElementById('libraryModal');
    const btnCloseLibrary = document.getElementById('btnCloseLibrary');
    const btnSaveCurrent = document.getElementById('btnSaveCurrent');
    const btnClearHistory = document.getElementById('btnClearHistory');
    const libraryStatus = document.getElementById('libraryStatus');
    const playlistItems = document.getElementById('playlistItems');
    const historyItems = document.getElementById('historyItems');
    const playlistEmpty = document.getElementById('playlistEmpty');
    const historyEmpty = document.getElementById('historyEmpty');
    const playlistCount = document.getElementById('playlistCount');
    const sleepModal = document.getElementById('sleepModal');
    const btnCloseSleep = document.getElementById('btnCloseSleep');
    const btnStartSleep = document.getElementById('btnStartSleep');
    const btnCancelSleep = document.getElementById('btnCancelSleep');
    const sleepDuration = document.getElementById('sleepDuration');
    const sleepStatus = document.getElementById('sleepStatus');

    // Web Audio API Setup: 7-Band Equalizer
    let audioCtx = null;
    let sourceNode = null;
    let eqFilters = [];
    const eqGains = [0, 0, 0, 0, 0, 0, 0];
    const eqFrequencies = [60, 150, 400, 1000, 2500, 6000, 14000];

    function setPlaybackIcon(isPlaying) {
      playIcon.innerHTML = isPlaying
        ? '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 5h4v14H7zM15 5h4v14h-4z"/></svg>'
        : '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
      btnPlayPause.setAttribute('aria-label', isPlaying ? 'Tạm dừng' : 'Phát nhạc');
      btnPlayPause.title = isPlaying ? 'Tạm dừng' : 'Phát nhạc';
    }
    setPlaybackIcon(false);

    const eqPresets = {
      flat: [0, 0, 0, 0, 0, 0, 0],
      pop: [-1, 2, 4, 3, 1, -1, -2],
      rock: [5, 3, -1, 2, 4, 3, 2],
      jazz: [3, 2, 1, 2, -1, 2, 3],
      classical: [4, 3, 2, 0, -1, 2, 4],
      edm: [6, 4, 1, 0, 2, 4, 5],
      acoustic: [2, 1, 0, 2, 3, 2, 1],
      hiphop: [6, 5, 1, -1, 2, 1, 3]
    };

    function updateEqBand(index, gain) {
      const normalizedGain = Math.max(-12, Math.min(12, Math.round(gain)));
      eqGains[index] = normalizedGain;
      const column = document.querySelector(`.eq-column[data-band="${index}"]`);
      const slider = column.querySelector('.vertical-slider');
      const label = column.querySelector('.eq-db-label');
      slider.value = normalizedGain;
      label.textContent = `${normalizedGain > 0 ? '+' : ''}${normalizedGain}dB`;
      if (eqFilters[index]) eqFilters[index].gain.value = normalizedGain;
    }

    function applyEqPreset(presetName) {
      const gains = eqPresets[presetName];
      if (!gains) return;
      gains.forEach((gain, index) => updateEqBand(index, gain));
    }

    function initAudioContext() {
      if (audioCtx) return;
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      audioCtx = new AudioContext();
      sourceNode = audioCtx.createMediaElementSource(audio);

      eqFilters = eqFrequencies.map((freq, index) => {
        const filter = audioCtx.createBiquadFilter();
        if (index === 0) {
          filter.type = 'lowshelf';
        } else if (index === eqFrequencies.length - 1) {
          filter.type = 'highshelf';
        } else {
          filter.type = 'peaking';
          filter.Q.value = 1.2;
        }
        filter.frequency.value = freq;
        filter.gain.value = eqGains[index];
        return filter;
      });

      sourceNode.connect(eqFilters[0]);
      for (let i = 0; i < eqFilters.length - 1; i++) {
        eqFilters[i].connect(eqFilters[i + 1]);
      }
      eqFilters[eqFilters.length - 1].connect(audioCtx.destination);
    }

    function formatTime(sec) {
      if (isNaN(sec)) return "00:00";
      const m = Math.floor(sec / 60);
      const s = Math.floor(sec % 60);
      return `${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}`;
    }

    const PLAYLIST_STORAGE_KEY = 'glassAudioPlaylist';
    const HISTORY_STORAGE_KEY = 'glassAudioHistory';
    let currentTrack = null;
    let playlist = [];
    let history = [];
    let sleepTimerDeadline = 0;
    let sleepTimerInterval = null;

    function setLibraryStatus(message, isError = false) {
      libraryStatus.textContent = message;
      libraryStatus.classList.toggle('hidden', !message);
      libraryStatus.classList.toggle('text-rose-300', isError);
      libraryStatus.classList.toggle('text-emerald-300', Boolean(message) && !isError);
    }

    function readTrackCollection(storageKey) {
      const raw = localStorage.getItem(storageKey);
      if (raw === null) return [];
      const records = JSON.parse(raw);
      if (!Array.isArray(records) || records.some(track =>
        !track || typeof track.url !== 'string' || typeof track.title !== 'string'
      )) {
        throw new Error('Dữ liệu danh sách nhạc đã lưu không hợp lệ.');
      }
      return records;
    }

    function persistTrackCollection(storageKey, records) {
      try {
        localStorage.setItem(storageKey, JSON.stringify(records));
        setLibraryStatus('');
        return true;
      } catch (err) {
        setLibraryStatus(`Không thể lưu dữ liệu trên thiết bị: ${err.message}`, true);
        return false;
      }
    }

    function renderTrackList(records, container, emptyState, storageKey) {
      container.replaceChildren();
      emptyState.classList.toggle('hidden', records.length > 0);
      records.forEach(track => {
        const row = document.createElement('div');
        row.className = 'library-row';

        const playButton = document.createElement('button');
        playButton.type = 'button';
        playButton.className = 'library-row-play';
        const title = document.createElement('strong');
        title.textContent = track.title;
        const artist = document.createElement('span');
        const creator = track.artist || 'YouTube Audio';
        const timestamp = track.playedAt || track.savedAt;
        artist.textContent = timestamp
          ? `${creator} · ${new Date(timestamp).toLocaleString()}`
          : creator;
        playButton.append(title, artist);
        playButton.addEventListener('click', () => {
          input.value = track.url;
          libraryModal.classList.replace('flex', 'hidden');
          form.requestSubmit();
        });

        const removeButton = document.createElement('button');
        removeButton.type = 'button';
        removeButton.className = 'library-row-remove';
        removeButton.textContent = '×';
        removeButton.setAttribute('aria-label', `Xóa ${track.title}`);
        removeButton.addEventListener('click', () => {
          const nextRecords = records.filter(item => item.url !== track.url);
          if (!persistTrackCollection(storageKey, nextRecords)) return;
          if (storageKey === PLAYLIST_STORAGE_KEY) playlist = nextRecords;
          else history = nextRecords;
          renderLibrary();
        });

        row.append(playButton, removeButton);
        container.append(row);
      });
    }

    function renderLibrary() {
      playlistCount.textContent = `${playlist.length} bài`;
      renderTrackList(playlist, playlistItems, playlistEmpty, PLAYLIST_STORAGE_KEY);
      renderTrackList(history, historyItems, historyEmpty, HISTORY_STORAGE_KEY);
    }

    function addTrackToCollection(storageKey, track) {
      const records = storageKey === PLAYLIST_STORAGE_KEY ? playlist : history;
      const updatedRecords = [track, ...records.filter(item => item.url !== track.url)];
      if (!persistTrackCollection(storageKey, updatedRecords)) return false;
      if (storageKey === PLAYLIST_STORAGE_KEY) playlist = updatedRecords;
      else history = updatedRecords;
      renderLibrary();
      return true;
    }

    try {
      playlist = readTrackCollection(PLAYLIST_STORAGE_KEY);
      history = readTrackCollection(HISTORY_STORAGE_KEY);
    } catch (err) {
      setLibraryStatus(`Không đọc được dữ liệu đã lưu: ${err.message}`, true);
    }
    renderLibrary();

    btnOpenLibrary.addEventListener('click', () => {
      renderLibrary();
      libraryModal.classList.replace('hidden', 'flex');
    });
    btnCloseLibrary.addEventListener('click', () => libraryModal.classList.replace('flex', 'hidden'));
    btnSaveCurrent.addEventListener('click', () => {
      if (!currentTrack) {
        setLibraryStatus('Hãy phát một bài trước khi lưu vào danh sách.', true);
        return;
      }
      if (addTrackToCollection(PLAYLIST_STORAGE_KEY, {
        ...currentTrack,
        savedAt: new Date().toISOString()
      })) {
        setLibraryStatus('Đã lưu bài hát vào danh sách phát.');
      }
    });
    btnClearHistory.addEventListener('click', () => {
      if (!history.length || !confirm('Xóa toàn bộ lịch sử nghe trên thiết bị này?')) return;
      if (persistTrackCollection(HISTORY_STORAGE_KEY, [])) {
        history = [];
        renderLibrary();
      }
    });

    function updateSleepTimer() {
      const remainingSeconds = Math.max(0, Math.ceil((sleepTimerDeadline - Date.now()) / 1000));
      if (!remainingSeconds) {
        clearInterval(sleepTimerInterval);
        sleepTimerInterval = null;
        sleepTimerDeadline = 0;
        audio.pause();
        sleepStatus.textContent = 'Đã hết giờ, phát nhạc đã tạm dừng.';
        btnOpenSleep.title = 'Hẹn giờ tự dừng';
        return;
      }
      const minutes = Math.floor(remainingSeconds / 60);
      const seconds = remainingSeconds % 60;
      const countdown = `${minutes}:${String(seconds).padStart(2, '0')}`;
      sleepStatus.textContent = `Nhạc sẽ dừng sau ${countdown}.`;
      btnOpenSleep.title = `Nhạc dừng sau ${countdown}`;
    }

    btnOpenSleep.addEventListener('click', () => sleepModal.classList.replace('hidden', 'flex'));
    btnCloseSleep.addEventListener('click', () => sleepModal.classList.replace('flex', 'hidden'));
    btnStartSleep.addEventListener('click', () => {
      const minutes = Number(sleepDuration.value);
      if (!Number.isFinite(minutes) || minutes <= 0) {
        sleepStatus.textContent = 'Thời gian hẹn phải lớn hơn 0.';
        return;
      }
      clearInterval(sleepTimerInterval);
      sleepTimerDeadline = Date.now() + minutes * 60 * 1000;
      updateSleepTimer();
      sleepTimerInterval = setInterval(updateSleepTimer, 1000);
      sleepModal.classList.replace('flex', 'hidden');
    });
    btnCancelSleep.addEventListener('click', () => {
      clearInterval(sleepTimerInterval);
      sleepTimerInterval = null;
      sleepTimerDeadline = 0;
      sleepStatus.textContent = 'Đã hủy hẹn giờ.';
      btnOpenSleep.title = 'Hẹn giờ tự dừng';
    });

    // Submit Tách âm thanh
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const sourceUrl = input.value.trim();
      loader.classList.remove('hidden');
      playerBox.classList.add('hidden');
      btnSubmit.disabled = true;

      try {
        const res = await fetch(`/api/extract?url=${encodeURIComponent(sourceUrl)}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Không thể tách âm thanh');

        songTitle.textContent = data.title;
        songArtist.textContent = data.artist;
        thumb.src = data.thumbnail || 'https://via.placeholder.com/300';
        
        audio.src = data.stream_url;
        // Gán link tải file cục bộ
        btnDownload.href = data.download_url;
        btnDownload.download = `${data.title}.m4a`;
        currentTrack = {
          url: sourceUrl,
          title: data.title || 'Bài hát không tên',
          artist: data.artist || 'YouTube Audio',
          thumbnail: data.thumbnail || ''
        };

        playerBox.classList.remove('hidden');
        form.classList.add('hidden');

        initAudioContext();
        if (audioCtx.state === 'suspended') audioCtx.resume();

        await audio.play();
        addTrackToCollection(HISTORY_STORAGE_KEY, {
          ...currentTrack,
          playedAt: new Date().toISOString()
        });

        if ('mediaSession' in navigator) {
          navigator.mediaSession.metadata = new MediaMetadata({
            title: data.title,
            artist: data.artist,
            artwork: [{ src: data.thumbnail, sizes: '512x512', type: 'image/jpeg' }]
          });
          navigator.mediaSession.setActionHandler('play', () => { audio.play(); });
          navigator.mediaSession.setActionHandler('pause', () => { audio.pause(); });
          navigator.mediaSession.setActionHandler('seekto', (details) => {
            if (details.seekTime) audio.currentTime = details.seekTime;
          });
        }
      } catch (err) {
        alert(err.message);
      } finally {
        loader.classList.add('hidden');
        btnSubmit.disabled = false;
      }
    });

    // Cập nhật thanh Seek Bar
    let isUserSeeking = false;
    audio.addEventListener('timeupdate', () => {
      if (!isUserSeeking && audio.duration) {
        seekBar.value = (audio.currentTime / audio.duration) * 100;
        currentTimeEl.textContent = formatTime(audio.currentTime);
      }
    });
    audio.addEventListener('loadedmetadata', () => {
      durationTimeEl.textContent = formatTime(audio.duration);
    });
    audio.addEventListener('play', () => { setPlaybackIcon(true); });
    audio.addEventListener('pause', () => { setPlaybackIcon(false); });
    seekBar.addEventListener('input', () => {
      isUserSeeking = true;
      if (audio.duration) {
        currentTimeEl.textContent = formatTime((seekBar.value / 100) * audio.duration);
      }
    });
    seekBar.addEventListener('change', () => {
      if (audio.duration) {
        audio.currentTime = (seekBar.value / 100) * audio.duration;
      }
      isUserSeeking = false;
    });

    // Play / Pause
    btnPlayPause.addEventListener('click', () => {
      if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
      if (audio.paused) {
        audio.play().catch(err => alert(`Không thể phát âm thanh: ${err.message}`));
      } else {
        audio.pause();
      }
    });

    // Tua 15s
    btnBackward.addEventListener('click', () => {
      audio.currentTime = Math.max(0, audio.currentTime - 15);
    });
    btnForward.addEventListener('click', () => {
      if (audio.duration) {
        audio.currentTime = Math.min(audio.duration, audio.currentTime + 15);
      }
    });
    audio.volume = Number(volumeBar.value);
    volumeBar.addEventListener('input', () => {
      audio.volume = Number(volumeBar.value);
    });
    btnRepeat.addEventListener('click', () => {
      audio.loop = !audio.loop;
      btnRepeat.classList.toggle('text-pink-300', audio.loop);
      btnRepeat.setAttribute('aria-label', audio.loop ? 'Tắt lặp lại' : 'Lặp lại');
    });

    function toggleUrlForm() {
      form.classList.toggle('hidden');
      if (!form.classList.contains('hidden')) input.focus();
    }
    btnToggleForm.addEventListener('click', toggleUrlForm);
    btnToggleFormMenu.addEventListener('click', toggleUrlForm);
    btnSettings.addEventListener('click', toggleUrlForm);

    // Quản lý Modal Tốc Độ
    btnOpenSpeed.addEventListener('click', () => speedModal.classList.replace('hidden', 'flex'));
    btnCloseSpeed.addEventListener('click', () => speedModal.classList.replace('flex', 'hidden'));
    
    document.querySelectorAll('.speed-opt').forEach(btn => {
      btn.addEventListener('click', () => {
        const speed = parseFloat(btn.dataset.speed);
        audio.playbackRate = speed;
        currentSpeedLabel.textContent = `${speed}x`;

        document.querySelectorAll('.speed-opt').forEach(b => {
          b.classList.remove('bg-pink-500/40', 'border-pink-400/50', 'text-white');
        });
        btn.classList.add('bg-pink-500/40', 'border-pink-400/50', 'text-white');
        speedModal.classList.replace('flex', 'hidden');
      });
    });

    // Quản lý Modal EQ
    btnOpenEQ.addEventListener('click', () => eqModal.classList.replace('hidden', 'flex'));
    btnCloseEQ.addEventListener('click', () => eqModal.classList.replace('flex', 'hidden'));

    // Xử lý từng cột EQ (+, -, Slider nhảy đúng 1dB)
    document.querySelectorAll('.eq-column').forEach(col => {
      const bandIndex = parseInt(col.dataset.band);
      const slider = col.querySelector('.vertical-slider');
      const btnPlus = col.querySelector('.btn-step-plus');
      const btnMinus = col.querySelector('.btn-step-minus');

      function updateGain(newGain) {
        updateEqBand(bandIndex, newGain);
        eqPreset.value = 'custom';
      }

      slider.addEventListener('input', (e) => {
        updateGain(parseFloat(e.target.value));
      });

      // Tăng chính xác 1 nấc (+1dB)
      btnPlus.addEventListener('click', () => {
        updateGain(parseFloat(slider.value) + 1);
      });

      // Giảm chính xác 1 nấc (-1dB)
      btnMinus.addEventListener('click', () => {
        updateGain(parseFloat(slider.value) - 1);
      });
    });

    eqPreset.addEventListener('change', () => {
      if (eqPreset.value !== 'custom') applyEqPreset(eqPreset.value);
    });

    // Reset toàn bộ EQ về 0dB
    btnResetEQ.addEventListener('click', () => {
      eqPreset.value = 'flat';
      applyEqPreset('flat');
    });

    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js')
          .catch(error => console.error('Không thể đăng ký Service Worker:', error));
      });
    }
  </script>
</body>
</html>
"""

_ICON_CACHE: dict[int, bytes] = {}


def _make_app_icon(size: int) -> bytes:
    cached_icon = _ICON_CACHE.get(size)
    if cached_icon is not None:
        return cached_icon

    pixels = bytearray()
    radius = size * 0.22
    center = size / 2
    play_triangle = (
        (size * 0.40, size * 0.29),
        (size * 0.70, size * 0.50),
        (size * 0.40, size * 0.71),
    )

    for y in range(size):
        pixels.append(0)
        for x in range(size):
            nearest_x = min(max(x, radius), size - radius)
            nearest_y = min(max(y, radius), size - radius)
            inside = (x - nearest_x) ** 2 + (y - nearest_y) ** 2 <= radius ** 2
            if not inside:
                pixels.extend((0, 0, 0, 0))
                continue

            blend = (x + y) / (2 * max(size - 1, 1))
            red = int(124 + 110 * blend)
            green = int(85 + 25 * (1 - blend))
            blue = int(211 - 12 * blend)

            ax, ay = play_triangle[0]
            bx, by = play_triangle[1]
            cx, cy = play_triangle[2]
            first = (x - bx) * (ay - by) - (ax - bx) * (y - by)
            second = (x - cx) * (by - cy) - (bx - cx) * (y - cy)
            third = (x - ax) * (cy - ay) - (cx - ax) * (y - ay)
            in_triangle = (first >= 0 and second >= 0 and third >= 0) or (
                first <= 0 and second <= 0 and third <= 0
            )
            if in_triangle:
                red, green, blue = 255, 255, 255

            ring_distance = abs(((x - center) ** 2 + (y - center) ** 2) ** 0.5 - size * 0.37)
            if ring_distance < size * 0.008 and not in_triangle:
                red = min(255, red + 45)
                green = min(255, green + 45)
                blue = min(255, blue + 45)
            pixels.extend((red, green, blue, 255))

    def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        chunk = chunk_type + data
        return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)

    png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(bytes(pixels), level=9))
        + png_chunk(b"IEND", b"")
    )
    _ICON_CACHE[size] = png
    return png


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_CONTENT


@app.get("/manifest.json")
def app_manifest():
    return JSONResponse(
        {
            "id": "/",
            "name": "Glass Audio - Trình nghe nhạc",
            "short_name": "Glass Audio",
            "description": "Trình nghe nhạc với giao diện kính.",
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "display_override": ["standalone"],
            "orientation": "portrait",
            "background_color": "#272044",
            "theme_color": "#272044",
            "icons": [
                {
                    "src": "/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any",
                },
                {
                    "src": "/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable",
                },
            ],
        }
    )


@app.get("/icon-192.png")
def app_icon_192():
    return Response(content=_make_app_icon(192), media_type="image/png")


@app.get("/icon-512.png")
def app_icon_512():
    return Response(content=_make_app_icon(512), media_type="image/png")


@app.get("/apple-touch-icon.png")
def apple_touch_icon():
    return Response(content=_make_app_icon(180), media_type="image/png")


@app.get("/service-worker.js")
def service_worker():
    worker_script = """
const CACHE_NAME = "glass-audio-shell-v1";
const APP_SHELL = "/";

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.add(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys
        .filter(key => key.startsWith("glass-audio-shell-") && key !== CACHE_NAME)
        .map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin || url.pathname !== APP_SHELL) {
    return;
  }

  event.respondWith(
    fetch(request)
      .then(response => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(APP_SHELL, copy));
        }
        return response;
      })
      .catch(() => caches.match(APP_SHELL))
  );
});
"""
    return Response(
        content=worker_script,
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/"},
    )


@app.get("/api/extract")
def extract_audio(url: str = Query(...)):
    # 1. Trích xuất Video ID từ link YouTube
    video_id_match = re.search(r'(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})', url)
    if not video_id_match:
        raise HTTPException(status_code=400, detail="Link YouTube không hợp lệ")
    video_id = video_id_match.group(1)

    # 2. Danh sách server proxy Invidious miễn phí
    invidious_instances = [
        "https://inv.tux.pizza",
        "https://invidious.nerdvpn.de",
        "https://invidious.jing.rocks"
    ]

    for instance in invidious_instances:
        try:
            res = requests.get(f"{instance}/api/v1/videos/{video_id}", timeout=6)
            if res.status_code == 200:
                data = res.json()
                # Lọc format âm thanh chất lượng tốt nhất
                audio_formats = [f for f in data.get("adaptiveFormats", []) if f.get("type", "").startswith("audio/")]
                if audio_formats:
                    # Chọn bitrate cao nhất
                    best_audio = sorted(audio_formats, key=lambda x: int(x.get("bitrate", 0)), reverse=True)[0]
                    audio_url = best_audio.get("url")
                    title = data.get("title", "Audio")
                    clean_title = re.sub(r'[\\/*?:"<>|]', "", title)

                    return JSONResponse({
                        "title": title,
                        "artist": data.get("author", "YouTube Audio"),
                        "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                        "stream_url": f"/api/proxy-audio?audio_src={requests.utils.quote(audio_url)}",
                        "download_url": f"/api/download?audio_src={requests.utils.quote(audio_url)}&filename={requests.utils.quote(clean_title)}"
                    })
        except Exception:
            continue

    raise HTTPException(status_code=500, detail="Không thể bóc tách luồng âm thanh từ các máy chủ trung gian")

@app.get("/api/proxy-audio")
def proxy_audio(request: Request, audio_src: str):
    """Proxy hỗ trợ Range Requests 206 để tua mượt"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"
        }
        range_header = request.headers.get("range")
        if range_header:
            headers["Range"] = range_header

        req = requests.get(audio_src, stream=True, headers=headers)
        response_headers = {
            "Accept-Ranges": "bytes",
            "Content-Type": req.headers.get("Content-Type", "audio/mp4"),
        }

        if "Content-Range" in req.headers:
            response_headers["Content-Range"] = req.headers["Content-Range"]
            status_code = 206
        else:
            status_code = req.status_code

        if "Content-Length" in req.headers:
            response_headers["Content-Length"] = req.headers["Content-Length"]

        return StreamingResponse(
            req.iter_content(chunk_size=1024 * 64),
            status_code=status_code,
            headers=response_headers,
            media_type=response_headers["Content-Type"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download")
def download_audio(audio_src: str, filename: str):
    """Chuyển thiết bị tải trực tiếp file audio từ máy chủ nguồn."""
    return RedirectResponse(url=audio_src)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)