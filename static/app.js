(() => {
  "use strict";

  const DEV = true;
  const ROW_HEIGHT = 72;
  const PAGE_SIZE = 50;
  const POOL_SIZE = 36;
  const OVERSCAN_ROWS = 8;
  const PREFETCH_PAGES = 2;
  const CACHE_MAX_PAGES = 14;
  const SWIPE_THRESHOLD = 60;
  const SWIPE_MAX = 140;

  const ICONS = {
    play: `<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`,
    pause: `<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>`,
    prev: `<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>`,
    next: `<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>`,
    shuffle: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 3h5v5M4 20L21 3M21 16v5h-5"/></svg>`,
    repeat: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 1l4 4-4 4M3 11V9a4 4 0 014-4h14M7 23l-4-4 4-4M21 13v2a4 4 0 01-4 4H3"/></svg>`,
    more: `<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/></svg>`,
    chevronDown: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>`,
    queue: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M3 12h18M3 18h12"/></svg>`,
    trash: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>`,
    edit: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
    plus: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"/></svg>`,
    download: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>`,
    link: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>`,
    alert: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>`,
    check: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>`,
    settings: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/></svg>`,
    chevronRight: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>`,
    chevronLeft: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>`,
  };

  const tracksViewport = document.querySelector("#tracksViewport");
  const tracksSpacer = document.querySelector("#tracksSpacer");
  const tracksRoot = document.querySelector("#tracks");
  const audio = document.querySelector("#audio");
  const playlistId = tracksViewport ? tracksViewport.dataset.playlistId : null;
  const isPlaylistPage = !!playlistId;

  if (!isPlaylistPage) {
    initHomePage();
    return;
  }

  if (audio) audio.preload = "none";

  const Toast = {
    container: null,
    init() {
      this.container = document.getElementById("toastStack");
      if (!this.container) {
        this.container = document.createElement("div");
        this.container.className = "toast-stack";
        this.container.id = "toastStack";
        document.body.appendChild(this.container);
      }
    },
    show(message, type = "info", duration = 3000, action = null) {
      if (!this.container) this.init();
      const el = document.createElement("div");
      el.className = `toast ${type}`;
      el.innerHTML = `<span>${escapeHtml(message)}</span>`;
      if (action) {
        const btn = document.createElement("button");
        btn.className = "toast-action";
        btn.textContent = action.label;
        btn.onclick = () => { action.callback(); this.dismiss(el); };
        el.appendChild(btn);
      }
      this.container.appendChild(el);
      if (duration > 0) setTimeout(() => this.dismiss(el), duration);
      return el;
    },
    success(m, d, a) { return this.show(m, "success", d, a); },
    error(m, d) { return this.show(m, "error", d); },
    info(m, d) { return this.show(m, "info", d); },
    dismiss(el) {
      if (!el.parentNode) return;
      el.classList.add("toast-exit");
      el.addEventListener("animationend", () => el.remove(), { once: true });
    }
  };
  Toast.init();

  const BottomSheet = {
    overlay: null, sheet: null, content: null, titleEl: null, isOpen: false, clearTimer: 0,
    init() {
      this.overlay = document.getElementById("bottomSheetOverlay");
      this.sheet = document.getElementById("bottomSheet");
      this.content = document.getElementById("bottomSheetContent");
      this.titleEl = document.getElementById("bottomSheetTitle");
      if (!this.overlay) return;
      this.overlay.addEventListener("click", () => this.close());
      const handle = this.sheet?.querySelector(".bs-handle");
      if (handle) {
        let startY = 0, currentY = 0, dragging = false;
        handle.addEventListener("touchstart", (e) => {
          startY = e.touches[0].clientY; dragging = true;
          this.sheet.style.transition = "none";
        }, { passive: true });
        handle.addEventListener("touchmove", (e) => {
          if (!dragging) return;
          currentY = e.touches[0].clientY;
          const delta = Math.max(0, currentY - startY);
          this.sheet.style.transform = `translateY(${delta}px)`;
        }, { passive: true });
        handle.addEventListener("touchend", () => {
          dragging = false;
          this.sheet.style.transition = "";
          if (currentY - startY > 100) this.close();
          else this.sheet.style.transform = "";
        });
      }
    },
    open(title, html) {
      if (!this.sheet) this.init();
      clearTimeout(this.clearTimer);
      this.titleEl.textContent = title || "";
      this.content.innerHTML = html;
      this.overlay.classList.add("is-open");
      this.sheet.classList.add("is-open");
      this.isOpen = true;
      document.body.style.overflow = "hidden";
    },
    close() {
      if (!this.sheet) return;
      this.sheet.classList.remove("is-open");
      this.overlay.classList.remove("is-open");
      this.isOpen = false;
      document.body.style.overflow = "";
      clearTimeout(this.clearTimer);
      this.clearTimer = setTimeout(() => { this.content.innerHTML = ""; }, 300);
    }
  };
  BottomSheet.init();

  const Queue = {
    list: [],
    history: [],
    maxHistory: 50,

    add(track) { this.list.push({ ...track }); },
    addNext(track) { this.list.unshift({ ...track }); },
    remove(index) { if (index >= 0 && index < this.list.length) this.list.splice(index, 1); },
    clear() { this.list = []; this.history = []; },
    next() {
      if (!this.list.length) return null;
      const track = this.list.shift();
      if (Player.currentTrack) {
        this.history.unshift({ ...Player.currentTrack });
        if (this.history.length > this.maxHistory) this.history.pop();
      }
      return track;
    },
    prev() {
      if (!this.history.length) return null;
      const track = this.history.shift();
      if (Player.currentTrack) this.list.unshift({ ...Player.currentTrack });
      return track;
    },
    peek(n = 5) { return this.list.slice(0, n); },
    count() { return this.list.length; }
  };

  const Player = {
    currentId: null,
    isPlaying: false,
    currentTrack: null,
    currentPlaylistIndex: null,

    init() {
      if (!audio) return;
      audio.addEventListener("play", () => { this.isPlaying = true; this.updateUI(); });
      audio.addEventListener("pause", () => { this.isPlaying = false; this.updateUI(); });
      audio.addEventListener("ended", () => this.playNext());
      audio.addEventListener("timeupdate", () => this.updateProgress());
      audio.addEventListener("loadedmetadata", () => this.updateDuration());
      audio.addEventListener("playing", () => {
        if (audio.dataset.needsFull) {
          const id = audio.dataset.needsFull;
          audio.dataset.needsFull = "";
          triggerFullDownload(id);
        }
      });

      const mini = document.getElementById("miniPlayer");
      if (mini) {
        mini.addEventListener("click", (e) => {
          if (e.target.closest(".mini-player-btn") || e.target.closest("svg")) return;
          this.openFullscreen();
        });
      }

      const fsClose = document.getElementById("fsClose");
      if (fsClose) {
        fsClose.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); this.closeFullscreen(); });
        fsClose.addEventListener("touchend", (e) => { e.preventDefault(); e.stopPropagation(); this.closeFullscreen(); });
      }

      const fsPlayPause = document.getElementById("fsPlayPause");
      if (fsPlayPause) {
        fsPlayPause.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); this.togglePlay(); });
      }

      const fsPrev = document.getElementById("fsPrev");
      if (fsPrev) {
        fsPrev.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); this.playPrev(); });
      }

      const fsNext = document.getElementById("fsNext");
      if (fsNext) {
        fsNext.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); this.playNext(); });
      }

      document.getElementById("fsQueueBtn")?.addEventListener("click", () => showQueueSheet());

      const scrubber = document.getElementById("fsScrubberTrack");
      if (scrubber) {
        scrubber.addEventListener("click", (e) => {
          const rect = scrubber.getBoundingClientRect();
          const pct = (e.clientX - rect.left) / rect.width;
          if (audio.duration) audio.currentTime = pct * audio.duration;
        });
      }

      const miniPlayPause = document.getElementById("miniPlayPause");
      if (miniPlayPause) {
        miniPlayPause.addEventListener("click", (e) => {
          e.stopPropagation();
          e.preventDefault();
          this.togglePlay();
        });
      }

      document.getElementById("playAllBtn")?.addEventListener("click", () => this.playAll());
      document.getElementById("shuffleBtn")?.addEventListener("click", () => this.shufflePlay());
    },

    play({ id, title, artist, cover, playlistIndex = null }) {
      if (!audio || !id) return;
      this.currentId = id;
      this.currentTrack = { id, title, artist, cover };
      this.currentPlaylistIndex = playlistIndex;
      this.isPlaying = true;

      const mini = document.getElementById("miniPlayer");
      document.getElementById("miniTitle").textContent = title || "";
      document.getElementById("miniArtist").textContent = artist || "";
      const miniCover = document.getElementById("miniCover");
      if (miniCover) { miniCover.src = cover || ""; miniCover.hidden = !cover; }
      mini?.classList.remove("is-hidden");

      document.getElementById("fsTitle").textContent = title || "";
      document.getElementById("fsArtist").textContent = artist || "";
      const fsCover = document.getElementById("fsCover");
      const fsBg = document.getElementById("fsBg");
      if (fsCover) fsCover.src = cover || "";
      if (fsBg) fsBg.style.backgroundImage = cover ? `url(${cover})` : "";

      const url = `/media/${id}/audio`;
      if (audio.dataset.trackId !== id) {
        audio.dataset.trackId = id;
        audio.src = url;
        audio.load();
      }
      const p = audio.play();
      if (p && p.catch) p.catch(() => {});
      VirtualList.setPlaying(id);
      this.updateUI();
    },

    stop() {
      if (!audio) return;
      audio.pause();
      audio.removeAttribute("src");
      audio.load();
      audio.dataset.trackId = "";
      this.currentId = null;
      this.currentTrack = null;
      this.currentPlaylistIndex = null;
      this.isPlaying = false;
      document.getElementById("miniPlayer")?.classList.add("is-hidden");
      VirtualList.setPlaying(null);
      this.updateUI();
    },

    togglePlay() {
      if (!audio) return;
      if (audio.paused) audio.play(); else audio.pause();
    },

    async playAll() {
      const tracks = await getAllReadyTracks();
      if (!tracks.length) { Toast.info("Нет готовых треков для воспроизведения"); return; }
      Queue.clear();
      tracks.slice(1).forEach(t => Queue.add(t));
      this.play({ ...tracks[0], playlistIndex: 0 });
      Toast.success(`Очередь: ${tracks.length} треков`);
    },

    async shufflePlay() {
      const tracks = await getAllReadyTracks();
      if (!tracks.length) { Toast.info("Нет готовых треков"); return; }
      Queue.clear();
      const shuffled = tracks.sort(() => Math.random() - 0.5);
      shuffled.slice(1).forEach(t => Queue.add(t));
      this.play({ ...shuffled[0], playlistIndex: null });
      Toast.success(`Перемешано: ${shuffled.length} треков`);
    },

    playNext() {
      const next = Queue.next();
      if (next) { this.play(next); return; }
      this.autoAdvance();
    },

    playPrev() {
      const prev = Queue.prev();
      if (prev) { this.play(prev); return; }
      Toast.info("Нет предыдущих треков");
    },

    autoAdvance() {
      if (this.currentPlaylistIndex != null) {
        const nextIndex = this.currentPlaylistIndex + 1;
        const track = PageCache.getTrack(nextIndex);
        if (track && track.status === "done") {
          this.play({ id: track.id, title: track.title, artist: track.artist, cover: `/media/${track.id}/cover`, playlistIndex: nextIndex });
          return;
        }
        this.tryFetchAndPlay(nextIndex);
        return;
      }
      this.stop();
      Toast.info("Очередь завершена");
    },

    async tryFetchAndPlay(index) {
      const page = Math.floor(index / PAGE_SIZE);
      await FetchScheduler.fetchPage(page).catch(() => null);
      const track = PageCache.getTrack(index);
      if (track && track.status === "done") {
        this.play({ id: track.id, title: track.title, artist: track.artist, cover: `/media/${track.id}/cover`, playlistIndex: index });
      } else {
        this.stop();
        Toast.info("Очередь завершена");
      }
    },

    openFullscreen() { document.getElementById("fullscreenPlayer")?.classList.add("is-open"); },
    closeFullscreen() { document.getElementById("fullscreenPlayer")?.classList.remove("is-open"); },

    updateUI() {
      const miniBtn = document.getElementById("miniPlayPause");
      const fsBtn = document.getElementById("fsPlayPause");
      if (miniBtn) miniBtn.innerHTML = this.isPlaying ? ICONS.pause : ICONS.play;
      if (fsBtn) fsBtn.innerHTML = this.isPlaying ? ICONS.pause : ICONS.play;
    },

    updateProgress() {
      if (!audio || !audio.duration) return;
      const pct = audio.currentTime / audio.duration;
      const fill = document.getElementById("fsScrubberFill");
      const thumb = document.getElementById("fsScrubberThumb");
      const cur = document.getElementById("fsCurrentTime");
      if (fill) fill.style.width = `${pct * 100}%`;
      if (thumb) thumb.style.left = `${pct * 100}%`;
      if (cur) cur.textContent = formatTime(audio.currentTime);
    },

    updateDuration() {
      const total = document.getElementById("fsTotalTime");
      if (total && audio.duration) total.textContent = formatTime(audio.duration);
    }
  };
  Player.init();

  function formatTime(s) {
    if (!isFinite(s)) return "0:00";
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  }

  async function getAllReadyTracks() {
    const out = [];
    const totalPages = Math.ceil(VirtualList.total / PAGE_SIZE);
    for (let p = 0; p < Math.min(totalPages, 20); p++) {
      const tracks = await FetchScheduler.fetchPage(p);
      if (tracks) {
        out.push(...tracks.filter(t => t.has_short || t.has_full || t.status === "done" || t.status === "done_short").map(t => ({
          id: t.id, title: t.title, artist: t.artist, cover: `/media/${t.id}/cover`
        })));
      }
    }
    return out;
  }

  function showQueueSheet() {
    const current = Player.currentTrack;
    const upcoming = Queue.peek(50);

    let html = '';
    if (current) {
      html += `<div style="display:flex;align-items:center;gap:12px;padding:12px 16px;background:color-mix(in srgb,var(--accent)8%,var(--panel));border-radius:12px;margin-bottom:8px;border:1px solid color-mix(in srgb,var(--accent)20%,var(--line));">
        <div style="width:40px;height:40px;border-radius:6px;background:var(--elevated);overflow:hidden;flex-shrink:0;">
          <img src="${escapeHtml(current.cover || '')}" style="width:100%;height:100%;object-fit:cover;" alt="">
        </div>
        <div style="flex:1;min-width:0;">
          <div style="font-weight:700;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(current.title)}</div>
          <div style="font-size:13px;color:var(--accent);">▶ Сейчас играет</div>
        </div>
      </div>`;
    }

    if (!upcoming.length) {
      html += `<div class="empty-state" style="padding:32px 0;"><div class="empty-state-title">Очередь пуста</div><div class="empty-state-text">Добавьте треки через меню «Ещё»</div></div>`;
    } else {
      html += `<div style="display:flex;flex-direction:column;gap:2px;">`;
      upcoming.forEach((t, i) => {
        html += `<div class="bs-item" style="padding:0 12px;height:56px;" data-queue-idx="${i}">
          <div style="width:40px;height:40px;border-radius:6px;background:var(--elevated);overflow:hidden;flex-shrink:0;">
            <img src="${escapeHtml(t.cover || '')}" style="width:100%;height:100%;object-fit:cover;" alt="">
          </div>
          <div style="flex:1;min-width:0;display:flex;flex-direction:column;justify-content:center;gap:2px;">
            <div style="font-weight:600;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(t.title)}</div>
            <div style="font-size:13px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(t.artist || '')}</div>
          </div>
          <button class="track-more-btn" style="color:var(--danger);width:36px;height:36px;" data-queue-remove="${i}" aria-label="Удалить из очереди">
            ${ICONS.trash}
          </button>
        </div>`;
      });
      html += `</div>`;
      if (Queue.list.length > 50) {
        html += `<div style="text-align:center;padding:12px;color:var(--muted);font-size:13px;">+${Queue.list.length - 50} треков</div>`;
      }
    }

    BottomSheet.open(`Очередь · ${Queue.count()}`, html);

    BottomSheet.content.querySelectorAll("[data-queue-remove]").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const idx = +btn.dataset.queueRemove;
        Queue.remove(idx);
        BottomSheet.close();
        setTimeout(() => showQueueSheet(), 200);
      });
    });

    BottomSheet.content.querySelectorAll("[data-queue-idx]").forEach(row => {
      row.addEventListener("click", () => {
        const idx = +row.dataset.queueIdx;
        const toPlay = Queue.list[idx];
        if (!toPlay) return;
        if (Player.currentTrack) Queue.history.unshift({ ...Player.currentTrack });
        Queue.list = Queue.list.slice(idx + 1);
        Player.play(toPlay);
        BottomSheet.close();
      });
    });
  }

  const Gestures = {
    init() {
      let startX = 0, startY = 0, currentRow = null, currentDelta = 0, isSwiping = false;

      tracksRoot.addEventListener("touchstart", (e) => {
        const row = e.target.closest(".track-row");
      }, { passive: true });

      tracksRoot.addEventListener("touchmove", (e) => {
        if (!currentRow) return;
      }, { passive: false });

      tracksRoot.addEventListener("touchend", () => {
        if (!currentRow || !isSwiping) { currentRow = null; return; }
        currentRow = null;
      });

      window.addEventListener("scroll", () => this.closeAll(), { passive: true });
      document.addEventListener("touchstart", (e) => {
        if (!e.target.closest(".track-row")) this.closeAll();
      }, { passive: true });

      tracksRoot.addEventListener("click", (e) => {
        const btn = e.target.closest(".swipe-action");
        if (!btn) return;
        e.stopPropagation();
        const row = btn.closest(".track-row");
        if (!row) return;
        const trackId = row.dataset.id;
        const title = row.dataset.title;
        const artist = row.dataset.artist;
        const cover = `/media/${trackId}/cover`;
        if (btn.classList.contains("delete")) confirmDeleteTrack(trackId);
        else if (btn.classList.contains("play-next")) {
          Queue.addNext({ id: trackId, title, artist, cover });
          Toast.success(`«${title}» - далее`);
          this.closeAll();
        }
        else if (btn.classList.contains("add")) {
          Queue.add({ id: trackId, title, artist, cover });
          Toast.success(`«${title}» - в очередь`);
          this.closeAll();
        }
      });
    },
    closeAll() {
      document.querySelectorAll(".track-row[data-swipe-open]").forEach(row => {
        const content = row.querySelector(".row-content");
        if (content) content.style.transform = "";
        delete row.dataset.swipeOpen;
      });
    }
  };
  Gestures.init();

  const perf = {
    marks: {},
    mark(n) { if (!DEV) return; this.marks[n] = performance.now(); },
    measure(name, start) {
      if (!DEV) return 0;
      const ms = performance.now() - (this.marks[start] || performance.now());
      console.log(`[perf] ${name}: ${ms.toFixed(1)}ms`);
      return ms;
    },
    log(...a) { if (DEV) console.log("[perf]", ...a); }
  };

  const PageCache = {
    pages: new Map(),
    touch(page) {
      const hit = this.pages.get(page);
      if (!hit) return null;
      hit.at = performance.now();
      return hit.tracks;
    },
    set(page, tracks) { this.pages.set(page, { tracks, at: performance.now(), stale: false }); this.evict(); },
    has(page) { return this.pages.has(page); },
    isStale(page) { const hit = this.pages.get(page); return Boolean(hit && hit.stale); },
    markStale(page) { const hit = this.pages.get(page); if (hit) hit.stale = true; },
    markRangeStale(s, e) {
      const fp = Math.max(0, Math.floor(s / PAGE_SIZE));
      const lp = Math.max(fp, Math.floor(e / PAGE_SIZE));
      for (let p = fp; p <= lp; p++) this.markStale(p);
    },
    invalidate() { this.pages.clear(); },
    evict(keepAround = null) {
      if (this.pages.size <= CACHE_MAX_PAGES) return;
      const entries = [...this.pages.entries()];
      if (keepAround != null) {
        entries.sort((a, b) => {
          const da = Math.abs(a[0] - keepAround), db = Math.abs(b[0] - keepAround);
          if (da !== db) return db - da;
          return a[1].at - b[1].at;
        });
      } else entries.sort((a, b) => a[1].at - b[1].at);
      while (this.pages.size > CACHE_MAX_PAGES && entries.length) this.pages.delete(entries.shift()[0]);
    },
    getTrack(index) {
      const page = Math.floor(index / PAGE_SIZE);
      const tracks = this.touch(page);
      if (!tracks) return null;
      return tracks[index % PAGE_SIZE] || null;
    },
    getAllCachedTracks() {
      const all = [];
      const sortedPages = [...this.pages.keys()].sort((a, b) => a - b);
      for (const p of sortedPages) {
        const tracks = this.pages.get(p).tracks || [];
        all.push(...tracks.map((t, idx) => ({ track: t, absoluteIndex: p * PAGE_SIZE + idx })));
      }
      return all;
    }
  };

  const FetchScheduler = {
    generation: 0,
    inflight: new Map(),
    async fetchPage(page, { priority = 0, generation = null, force = false } = {}) {
      const gen = generation == null ? this.generation : generation;
      if (!force && PageCache.has(page) && !PageCache.isStale(page)) return PageCache.touch(page);
      if (this.inflight.has(page)) {
        try { return await this.inflight.get(page).promise; } catch { return PageCache.touch(page); }
      }
      const controller = new AbortController();
      const offset = page * PAGE_SIZE;
      const promise = (async () => {
        const t0 = performance.now();
        const res = await fetch(`/api/playlists/${playlistId}/tracks?offset=${offset}&limit=${PAGE_SIZE}&align=1`, { signal: controller.signal, cache: "no-store" });
        if (!res.ok) throw new Error(`page ${page} ${res.status}`);
        const payload = await res.json();
        if (gen !== this.generation) return PageCache.touch(page);
        if (typeof payload.total === "number") VirtualList.setTotal(payload.total);
        PageCache.set(page, payload.tracks || []);
        if (DEV && payload.server_ms != null) perf.log(`page ${page}: net=${(performance.now() - t0).toFixed(1)}ms server=${payload.server_ms}ms`);
        return payload.tracks || [];
      })();
      this.inflight.set(page, { controller, promise, priority, gen });
      try { return await promise; } catch (err) {
        if (err.name === "AbortError") return PageCache.touch(page);
        return PageCache.touch(page);
      } finally {
        const cur = this.inflight.get(page);
        if (cur && cur.gen === gen) this.inflight.delete(page);
      }
    },
    bump() {
      this.generation += 1;
      for (const [, job] of this.inflight) job.controller.abort();
      this.inflight.clear();
      return this.generation;
    },
    cancelDistant(centerPage, keepRadius = PREFETCH_PAGES + 2) {
      for (const [page, job] of [...this.inflight.entries()]) {
        if (Math.abs(page - centerPage) > keepRadius) { job.controller.abort(); this.inflight.delete(page); }
      }
    },
    async ensureRange(startIndex, endIndex, { prefetch = true, force = false } = {}) {
      const gen = this.generation;
      const firstPage = Math.max(0, Math.floor(startIndex / PAGE_SIZE));
      const lastPage = Math.max(firstPage, Math.floor(endIndex / PAGE_SIZE));
      const center = Math.floor((firstPage + lastPage) / 2);
      this.cancelDistant(center);
      const needed = [];
      for (let p = firstPage; p <= lastPage; p++) if (force || !PageCache.has(p) || PageCache.isStale(p)) needed.push({ page: p, priority: 0 });
      if (prefetch) {
        for (let p = firstPage - PREFETCH_PAGES; p < firstPage; p++) if (p >= 0 && (!PageCache.has(p) || PageCache.isStale(p))) needed.push({ page: p, priority: 1 });
        for (let p = lastPage + 1; p <= lastPage + PREFETCH_PAGES; p++) if (!PageCache.has(p) || PageCache.isStale(p)) needed.push({ page: p, priority: 1 });
      }
      needed.sort((a, b) => a.priority - b.priority || Math.abs(a.page - center) - Math.abs(b.page - center));
      await Promise.all(needed.map(({ page, priority }) => this.fetchPage(page, { priority, generation: gen, force }).catch(() => PageCache.touch(page))));
      PageCache.evict(center);
    }
  };

  const VirtualList = {
    total: 0, pool: [], firstIndex: 0, playingId: null,
    scrollRaf: 0, fetchRaf: 0, filter: "",
    init() {
      tracksRoot.textContent = "";
      tracksRoot.classList.add("tracks-recycled");
      for (let i = 0; i < POOL_SIZE; i++) {
        const row = createRowElement();
        row.hidden = true;
        tracksRoot.appendChild(row);
        this.pool.push(row);
      }
      this.bindScroll();
    },
    setTotal(n) {
      const next = Math.max(0, Number(n) || 0);
      if (next === this.total) return;
      this.total = next;
      if (!this.filter) {
        tracksSpacer.style.height = `${Math.max(next, 1) * ROW_HEIGHT}px`;
      }
      this.paint(true);
      const skel = document.getElementById("skeletonContainer");
      if (skel && next > 0) skel.hidden = true;
    },
    setPlaying(id) {
      this.playingId = id;
      for (const row of this.pool) {
        if (row.hidden) continue;
        row.classList.toggle("is-playing", row.dataset.id === id);
      }
    },
    setFilter(text) {
      this.filter = text.toLowerCase().trim();
      this.paint(true);
    },
    viewportRange() {
      const top = tracksViewport.getBoundingClientRect().top;
      const scrollY = Math.max(0, -top);
      const viewH = window.innerHeight;
      const start = Math.max(0, Math.floor(scrollY / ROW_HEIGHT) - OVERSCAN_ROWS);
      const end = Math.min(Math.max(this.total - 1, 0), Math.ceil((scrollY + viewH) / ROW_HEIGHT) + OVERSCAN_ROWS);
      return { start, end, scrollY };
    },
    paint(force = false) {
      const t0 = performance.now();
      if (!this.total) {
        for (const row of this.pool) row.hidden = true;
        this.showEmpty();
        return;
      }
      const empty = tracksRoot.querySelector(".empty-state");
      if (empty) empty.remove();

      if (this.filter) {
        const cached = PageCache.getAllCachedTracks();
        const matches = cached.filter(item => {
          const t = (item.track.title || "").toLowerCase();
          const a = (item.track.artist || "").toLowerCase();
          return t.includes(this.filter) || a.includes(this.filter);
        });

        tracksSpacer.style.height = `${Math.max(matches.length, 1) * ROW_HEIGHT}px`;

        if (!matches.length) {
          for (const row of this.pool) row.hidden = true;
          this.showEmpty("Ничего не найдено");
          return;
        }

        const { start, end } = this.viewportRange();
        for (let i = 0; i < this.pool.length; i++) {
          const row = this.pool[i];
          const matchIndex = start + i;
          if (matchIndex > end || matchIndex >= matches.length) {
            row.hidden = true;
            continue;
          }
          row.hidden = false;
          row.style.transform = `translate3d(0, ${matchIndex * ROW_HEIGHT}px, 0)`;
          const { track, absoluteIndex } = matches[matchIndex];
          bindRow(row, track, absoluteIndex, this.playingId);
        }
        return;
      }

      tracksSpacer.style.height = `${Math.max(this.total, 1) * ROW_HEIGHT}px`;
      const { start, end } = this.viewportRange();
      const count = Math.min(this.pool.length, Math.max(0, end - start + 1));
      this.firstIndex = start;

      for (let i = 0; i < this.pool.length; i++) {
        const row = this.pool[i];
        const index = start + i;
        if (index > end || index >= this.total) { row.hidden = true; continue; }
        row.hidden = false;
        row.style.transform = `translate3d(0, ${index * ROW_HEIGHT}px, 0)`;
        const track = PageCache.getTrack(index);
        bindRow(row, track, index, this.playingId);
      }
      if (DEV && force) perf.log(`paint rows=${count} ${(performance.now() - t0).toFixed(2)}ms`);
    },
    showEmpty(title = "Плейлист пуст") {
      let empty = tracksRoot.querySelector(".empty-state");
      if (empty) {
        empty.querySelector(".empty-state-title").textContent = title;
        return;
      }
      empty = document.createElement("div");
      empty.className = "empty-state";
      empty.innerHTML = `<div class="empty-state-icon">🎵</div><div class="empty-state-title">${escapeHtml(title)}</div><div class="empty-state-text">Добавьте треки из Яндекс Музыки</div>`;
      tracksRoot.appendChild(empty);
    },
    schedulePaint() {
      if (this.scrollRaf) return;
      this.scrollRaf = requestAnimationFrame(() => { this.scrollRaf = 0; this.paint(); this.scheduleFetch(); });
    },
    scheduleFetch() {
      if (this.fetchRaf) cancelAnimationFrame(this.fetchRaf);
      this.fetchRaf = requestAnimationFrame(() => {
        this.fetchRaf = 0;
        const { start, end } = this.viewportRange();
        FetchScheduler.ensureRange(start, end).then(() => this.paint());
      });
    },
    bindScroll() {
      window.addEventListener("scroll", () => { Gestures.closeAll(); this.schedulePaint(); }, { passive: true });
      window.addEventListener("resize", () => this.paint(true), { passive: true });
    }
  };

  function createRowElement() {
    const row = document.createElement("article");
    row.className = "track track-row";
    row.innerHTML = `
      <div class="row-content">
        <div class="track-cover-wrap">
          <img class="track-cover" alt="" loading="lazy" decoding="async">
          <div class="track-num-overlay">…</div>
          <button class="track-play-btn" type="button" aria-label="Воспроизвести">${ICONS.play}</button>
          <span class="cover-spinner" hidden aria-hidden="true"></span>
        </div>
        <div class="track-main">
          <div class="marquee track-title"><span class="t-title">…</span></div>
          <div class="marquee track-artist"><span class="t-artist"></span></div>
        </div>
        <div class="track-right">
          <div class="track-status-icon t-status-icon"></div>
          <button class="track-more-btn" type="button" aria-label="Ещё">${ICONS.more}</button>
        </div>
      </div>`;
    return row;
  }

  function bindRow(row, track, index, playingId) {
    if (!track) {
      if (row.dataset.placeholder === "1" && row.dataset.index === String(index)) return;
      row.dataset.placeholder = "1";
      row.dataset.index = String(index);
      row.dataset.id = "";
      row.classList.add("is-placeholder");
      row.classList.remove("ready", "is-playing", "is-downloading");
      row.querySelector(".t-title").textContent = "Загрузка…";
      row.querySelector(".t-artist").textContent = "";
      row.querySelector(".t-status-icon").innerHTML = "";
      row.querySelector(".track-num-overlay").textContent = String(index + 1);
      row.querySelector(".track-cover").removeAttribute("src");
      row.querySelector(".track-play-btn").disabled = true;
      const prog = row.querySelector(".download-progress");
      if (prog) prog.remove();
      return;
    }

    const fp = `${track.id}:${track.status}:${track.error || ""}:${track.title}:${track.artist}`;
    if (row.dataset.fp === fp && row.dataset.index === String(index)) {
      row.classList.toggle("is-playing", track.id === playingId);
      updatePlayingState(row, track.id === playingId);
      return;
    }

    row.dataset.fp = fp;
    row.dataset.index = String(index);
    row.dataset.id = track.id;
    row.dataset.title = track.title || "";
    row.dataset.artist = track.artist || "";
    row.dataset.placeholder = "0";
    row.classList.remove("is-placeholder");
    const isPlayable = track.status === "done" || track.status === "done_short" || track.status === "downloading_full";
    const isDownloading = track.status === "downloading" || track.status === "downloading_short" || track.status === "downloading_full";
    const isShortOnly = track.status === "done_short" || track.status === "downloading_full";
    row.classList.toggle("ready", isPlayable);
    row.classList.toggle("is-playing", track.id === playingId);
    row.classList.toggle("is-downloading", isDownloading);
    row.classList.toggle("is-short-only", isShortOnly);

    function handlePlayClick(e) {
      if (e) e.stopPropagation();
      Player.play({ id: track.id, title: track.title, artist: track.artist, cover: coverUrl, playlistIndex: index });
      if (isShortOnly) audio.dataset.needsFull = track.id;
    }

    const titleSpan = row.querySelector(".t-title");
    const artistSpan = row.querySelector(".t-artist");
    titleSpan.textContent = track.title || "";
    artistSpan.textContent = track.artist || "";

    const coverUrl = `/media/${track.id}/cover`;
    const coverImg = row.querySelector(".track-cover");
    coverImg.src = coverUrl;
    coverImg.dataset.src = coverUrl;

    row.querySelector(".track-num-overlay").textContent = String(index + 1);

    const playBtn = row.querySelector(".track-play-btn");
    playBtn.disabled = !isPlayable;
    if (isPlayable) {
      playBtn.onclick = (e) => handlePlayClick(e);
    } else {
      playBtn.onclick = null;
    }

    const rowContent = row.querySelector(".row-content");
    rowContent.onclick = (e) => {
      if (e.target.closest(".track-more-btn") || e.target.closest(".track-play-btn")) return;
      if (isPlayable) handlePlayClick();
    };

    const statusIcon = row.querySelector(".t-status-icon");
    statusIcon.innerHTML = getStatusIcon(track);

    const loading = track.status === "queued" || track.status === "downloading" || track.status === "downloading_short" || track.status === "downloading_full";
    row.querySelector(".cover-spinner").hidden = !loading;

    let progressBar = row.querySelector(".download-progress");
    if (track.status === "downloading" || track.status === "downloading_short" || track.status === "downloading_full") {
      if (!progressBar) {
        progressBar = document.createElement("div");
        progressBar.className = "download-progress";
        progressBar.innerHTML = '<div class="download-progress-fill" style="width:0%"></div>';
        rowContent.appendChild(progressBar);
      }
      progressBar.querySelector(".download-progress-fill").style.width = "60%";
    } else if (progressBar) {
      progressBar.remove();
    }

    updatePlayingState(row, track.id === playingId);

    row.querySelector(".track-more-btn").onclick = (e) => {
      e.stopPropagation();
      showTrackOptions(track);
    };

    requestAnimationFrame(() => {
      updateMarquee(row.querySelector(".track-title"));
      updateMarquee(row.querySelector(".track-artist"));
    });
  }

  function updatePlayingState(row, isPlaying) {
    const numOverlay = row.querySelector(".track-num-overlay");
    const playBtn = row.querySelector(".track-play-btn");
    if (numOverlay) numOverlay.style.opacity = isPlaying ? "0" : "";
    if (playBtn) playBtn.style.opacity = isPlaying ? "1" : "";
  }

  function getStatusIcon(track) {
    if (track.status === "queued") return '<div class="status-dot"></div>';
    if (track.status === "error") return '<div class="status-error">!</div>';
    if (track.status === "downloading_short") return '<div class="status-dot" style="background:var(--accent)"></div>';
    if (track.status === "done_short") return '<div class="status-upgrade" title="Upgrading to full quality…">⟳</div>';
    if (track.status === "downloading_full") return '<div class="status-upgrade" title="Downloading full quality…">⟳</div>';
    return "";
  }

  async function triggerFullDownload(trackId) {
    try {
      await fetch(`/api/tracks/${trackId}/prioritize_full`, { method: "POST" });
    } catch {}
  }

  function updateMarquee(el) {
    if (!el) return;
    el.classList.remove("is-overflowing");
    const span = el.querySelector("span");
    if (!span) return;
    requestAnimationFrame(() => {
      const overflow = span.scrollWidth > el.clientWidth + 2;
      el.classList.toggle("is-overflowing", overflow);
    });
  }

  function showTrackOptions(track) {
    const cover = `/media/${track.id}/cover`;
    const isShortOnly = track.status === "done_short" || track.status === "downloading_full";
    const items = [
      { icon: ICONS.play, label: "Воспроизвести", action: () => { Player.play({ id: track.id, title: track.title, artist: track.artist, cover, playlistIndex: null }); if (isShortOnly) audio.dataset.needsFull = track.id; } },
      { icon: ICONS.next, label: "Воспроизвести далее", action: () => { Queue.addNext({ id: track.id, title: track.title, artist: track.artist, cover }); Toast.success(`«${track.title}» - далее`); } },
      { icon: ICONS.plus, label: "Добавить в очередь", action: () => { Queue.add({ id: track.id, title: track.title, artist: track.artist, cover }); Toast.success(`«${track.title}» - в очередь`); } },
      { icon: ICONS.link, label: "Открыть в Яндекс Музыке", action: () => window.open(`https://music.yandex.ru/track/${track.yandex_id || track.id}`, "_blank") },
      { icon: ICONS.trash, label: "Удалить трек", danger: true, action: () => confirmDeleteTrack(track.id) }
    ];
    const html = items.map((item, i) => `
      <button class="bs-item ${item.danger ? 'danger' : ''}" data-idx="${i}">
        <span class="bs-item-icon">${item.icon}</span><span>${escapeHtml(item.label)}</span>
      </button>`).join("");
    BottomSheet.open(track.title || "Трек", `<div class="bs-list">${html}</div>`);
    BottomSheet.content.querySelectorAll("[data-idx]").forEach(btn => {
      btn.onclick = () => { BottomSheet.close(); items[+btn.dataset.idx].action(); };
    });
  }

  async function confirmDeleteTrack(trackId) {
    BottomSheet.open("Удалить трек?", `
      <p style="color:var(--muted);margin:0 0 16px;font-size:14px;">Это действие нельзя отменить. Трек будет удалён навсегда.</p>
      <button class="bs-btn danger" id="confirmDelete">Удалить</button>
      <button class="bs-btn secondary" id="cancelDelete">Отмена</button>
    `);
    document.getElementById("confirmDelete")?.addEventListener("click", async () => {
      BottomSheet.close();
      await deleteTrack(trackId);
    });
    document.getElementById("cancelDelete")?.addEventListener("click", () => BottomSheet.close());
  }

  async function deleteTrack(trackId) {
    const res = await fetch(`/api/tracks/${trackId}`, { method: "DELETE" });
    if (!res.ok) { Toast.error("Не удалось удалить трек"); return; }
    Toast.success("Трек удалён", 5000, { label: "Отменить", callback: () => Toast.info("Отмена в разработке") });
    if (Player.currentId === trackId) Player.stop();
    PageCache.invalidate();
    FetchScheduler.bump();
    const meta = await fetch(`/api/playlists/${playlistId}`, { cache: "no-store" }).then(r => r.json());
    State.applySummary(meta);
    if (Number(meta.pending_count || 0) > 0 || meta.import_status === "importing") State.connectEvents();
  }

  const State = {
    playlist: null, es: null, refreshTimer: 0, lastRefreshAt: 0,
    applySummary(summary) {
      const prev = this.playlist;
      this.playlist = summary;

      const heroTitle = document.getElementById("playlistHeroTitle");
      const heroMeta = document.getElementById("playlistHeroMeta");
      const stickyTitle = document.getElementById("stickyTitle");
      if (heroTitle && summary.title) heroTitle.textContent = summary.title;
      if (stickyTitle && summary.title) stickyTitle.textContent = summary.title;
      if (heroMeta) {
        const total = Number(summary.track_count || 0);
        const done = Number(summary.done_count || 0);
        heroMeta.textContent = total > 0 ? `${total} треков · ${done} готово` : "Пустой плейлист";
      }

      const importCard = document.getElementById("importProgressCard");
      if (summary.import_status === "importing") {
        if (importCard) importCard.hidden = false;
        const count = Number(summary.track_count || 0);
        const it = document.getElementById("importProgressTitle");
        const isub = document.getElementById("importProgressSub");
        if (it) it.textContent = summary.title || "Импорт...";
        if (isub) isub.textContent = count > 0 ? `Найдено ${count} треков...` : "Импортируем...";
      } else if (importCard) {
        importCard.hidden = true;
      }

      const total = Number(summary.track_count || 0);
      VirtualList.setTotal(total);

      const changed = !prev || prev.tracks_updated_at !== summary.tracks_updated_at || prev.done_count !== summary.done_count || prev.pending_count !== summary.pending_count || prev.track_count !== summary.track_count;
      if (changed) this.scheduleSoftRefresh();
    },
    scheduleSoftRefresh() {
      const now = performance.now();
      const wait = Math.max(0, 1200 - (now - this.lastRefreshAt));
      clearTimeout(this.refreshTimer);
      this.refreshTimer = setTimeout(() => {
        this.lastRefreshAt = performance.now();
        const { start, end } = VirtualList.viewportRange();
        PageCache.markRangeStale(start, end);
        FetchScheduler.ensureRange(start, end, { prefetch: false, force: true }).then(() => VirtualList.paint(true)).catch(() => {});
      }, wait);
    },
    connectEvents() {
      if (this.es) { this.es.close(); this.es = null; }
      const es = new EventSource(`/api/playlists/${playlistId}/events`);
      this.es = es;
      es.addEventListener("playlist", (ev) => { try { this.applySummary(JSON.parse(ev.data)); } catch {} });
      es.addEventListener("idle", (ev) => { try { this.applySummary(JSON.parse(ev.data)); } catch {} es.close(); this.es = null; });
      es.onerror = () => {};
    }
  };

  function initPlaylistMenu() {
    const moreBtn = document.getElementById("playlistMoreBtn");
    const addTracksBtn = document.getElementById("addTracksBtn");
    if (!moreBtn) return;

    moreBtn.addEventListener("click", () => {
      const items = [
        { icon: ICONS.edit, label: "Переименовать", action: () => showRenameSheet() },
        { icon: ICONS.trash, label: "Удалить плейлист", danger: true, action: () => showDeletePlaylistSheet() },
        { icon: ICONS.check, label: "Обновить метаданные", action: () => { PageCache.invalidate(); FetchScheduler.bump(); VirtualList.paint(true); Toast.success("Обновлено"); } }
      ];
      const html = items.map((it, i) => `
        <button class="bs-item ${it.danger ? 'danger' : ''}" data-idx="${i}">
          <span class="bs-item-icon">${it.icon}</span><span>${escapeHtml(it.label)}</span>
        </button>`).join("");
      BottomSheet.open("Опции плейлиста", `<div class="bs-list">${html}</div>`);
      BottomSheet.content.querySelectorAll("[data-idx]").forEach(btn => {
        btn.onclick = () => { BottomSheet.close(); items[+btn.dataset.idx].action(); };
      });
    });

    document.getElementById("playlistHeroTitle")?.addEventListener("click", () => showRenameSheet());

    if (addTracksBtn) {
      addTracksBtn.addEventListener("click", () => {
        BottomSheet.open("Добавить треки", `
          <input class="bs-input" id="addTrackUrl" placeholder="Ссылка на трек, альбом или плейлист" inputmode="url">
          <button class="bs-btn" id="confirmAddTrack">Добавить</button>
        `);
        document.getElementById("confirmAddTrack")?.addEventListener("click", () => {
          const url = document.getElementById("addTrackUrl")?.value;
          if (!url) return;
          const form = document.createElement("form");
          form.method = "post";
          form.action = `/api/playlists/${playlistId}/add`;
          form.innerHTML = `<input name="url" value="${escapeHtml(url)}">`;
          document.body.appendChild(form);
          form.submit();
        });
      });
    }
  }

  function showRenameSheet() {
    const current = State.playlist?.title || "";
    BottomSheet.open("Переименовать", `
      <input class="bs-input" id="renameInput" value="${escapeHtml(current)}" maxlength="100" autofocus>
      <button class="bs-btn" id="confirmRename">Сохранить</button>
    `);

    const input = document.getElementById("renameInput");
    const confirmBtn = document.getElementById("confirmRename");

    const doRename = () => {
      const title = input?.value?.trim();
      if (!title) return;
      const form = document.createElement("form");
      form.method = "post";
      form.action = `/api/playlists/${playlistId}/rename`;
      form.innerHTML = `<input name="title" value="${escapeHtml(title)}">`;
      document.body.appendChild(form);
      form.submit();
    };

    confirmBtn?.addEventListener("click", doRename);
    input?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        doRename();
      }
    });
    input?.focus();
  }

  function showDeletePlaylistSheet() {
    const count = State.playlist?.track_count || 0;
    BottomSheet.open("Удалить плейлист?", `
      <p style="color:var(--muted);margin:0 0 16px;font-size:14px;">Будет удалено ${count} треков. Это действие нельзя отменить.</p>
      <button class="bs-btn danger" id="confirmDeletePlaylist">Удалить</button>
      <button class="bs-btn secondary" id="cancelDeletePlaylist">Отмена</button>
    `);
    document.getElementById("confirmDeletePlaylist")?.addEventListener("click", () => {
      const form = document.createElement("form");
      form.method = "post";
      form.action = `/api/playlists/${playlistId}/delete`;
      document.body.appendChild(form);
      form.submit();
    });
    document.getElementById("cancelDeletePlaylist")?.addEventListener("click", () => BottomSheet.close());
  }

  function initCollapsibleHeader() {
    const hero = document.getElementById("playlistHero");
    const sticky = document.getElementById("stickyHeader");
    if (!hero || !sticky) return;
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(e => sticky.classList.toggle("is-collapsed", !e.isIntersecting));
    }, { threshold: 0.1, rootMargin: "-60px 0px 0px 0px" });
    observer.observe(hero);
  }

  function initPullToRefresh() {
    const shell = document.querySelector(".shell");
    if (!shell) return;
    let startY = 0, pulling = false;
    const indicator = document.createElement("div");
    indicator.className = "ptr-indicator";
    shell.prepend(indicator);

    shell.addEventListener("touchstart", (e) => {
      if (window.scrollY > 5) return;
      startY = e.touches[0].clientY;
      pulling = true;
    }, { passive: true });

    shell.addEventListener("touchmove", (e) => {
      if (!pulling) return;
      const dy = e.touches[0].clientY - startY;
      if (dy > 0 && dy < 120) {
        indicator.classList.add("is-pulling");
        indicator.style.transform = `translateX(-50%) translateY(${dy * 0.4}px)`;
      }
    }, { passive: true });

    shell.addEventListener("touchend", () => {
      if (!pulling) return;
      pulling = false;
      const dy = parseFloat(indicator.style.transform?.match(/translateY\(([^)]+)\)/)?.[1] || 0);
      indicator.classList.remove("is-pulling");
      indicator.style.transform = "";
      if (dy > 40) {
        Toast.info("Обновление...");
        location.reload();
      }
    });
  }

  async function boot() {
    perf.mark("boot");
    VirtualList.init();
    VirtualList.paint(true);
    initCollapsibleHeader();
    initPlaylistMenu();
    initPullToRefresh();

    const meta = await fetch(`/api/playlists/${playlistId}`, { cache: "no-store" }).then(r => r.json());
    State.applySummary(meta);
    perf.measure("playlist-meta", "boot");

    const { start, end } = VirtualList.viewportRange();
    await FetchScheduler.ensureRange(start, end);
    VirtualList.paint(true);
    perf.measure("first-visible-filled", "boot");

    if (meta.import_status === "importing" || Number(meta.pending_count || 0) > 0) State.connectEvents();

    const searchInput = document.getElementById("trackSearch");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => VirtualList.setFilter(e.target.value));
    }
  }

  boot().catch(err => console.error(err));

  function initHomePage() {
    initPullToRefresh();

    checkImportStatus();

    document.querySelectorAll('.playlist-thumb[data-playlist-id]').forEach(img => {
      const pid = img.dataset.playlistId;
      fetch(`/api/playlists/${pid}/tracks?offset=0&limit=1`)
        .then(r => r.json())
        .then(data => {
          const firstTrack = data.tracks?.[0];
          if (firstTrack?.status === "done") {
            img.src = `/media/${firstTrack.id}/cover`;
          }
        })
        .catch(() => {});
    });

    const fab = document.getElementById("homeFab");
    if (fab) {
      fab.addEventListener("click", () => {
        BottomSheet.open("Новый плейлист", `
          <input class="bs-input" id="newPlaylistTitle" placeholder="Название плейлиста" maxlength="100">
          <button class="bs-btn" id="confirmCreate">Создать</button>
        `);
        document.getElementById("confirmCreate")?.addEventListener("click", () => {
          const title = document.getElementById("newPlaylistTitle")?.value;
          if (!title) return;
          const form = document.createElement("form");
          form.method = "post";
          form.action = "/api/playlists";
          form.innerHTML = `<input name="title" value="${escapeHtml(title)}">`;
          document.body.appendChild(form);
          form.submit();
        });
      });
    }

    const list = document.getElementById("playlistList");
    if (!list) return;
    let startX = 0, startY = 0, currentCard = null, currentDelta = 0, isSwiping = false;

    list.addEventListener("touchstart", (e) => {
      console.log();
    }, { passive: true });

    list.addEventListener("touchmove", (e) => {
      if (!currentCard) return;
    }, { passive: true });

    list.addEventListener("touchend", () => {
      if (!currentCard || !isSwiping) { currentCard = null; return; }
      const content = currentCard.querySelector(".playlist-row");
      if (Math.abs(currentDelta) > SWIPE_THRESHOLD) {
        const snapX = currentDelta > 0 ? SWIPE_MAX : -SWIPE_MAX;
        if (content) content.style.transform = `translateX(${snapX}px)`;
        currentCard.dataset.swipeOpen = currentDelta > 0 ? "right" : "left";
      } else {
        if (content) content.style.transform = "";
        delete currentCard.dataset.swipeOpen;
      }
      currentCard = null;
    });

    window.addEventListener("scroll", () => {
      document.querySelectorAll(".playlist-swipe-wrap[data-swipe-open]").forEach(card => {
        card.querySelector(".playlist-row").style.transform = "";
        delete card.dataset.swipeOpen;
      });
    }, { passive: true });

    list.addEventListener("click", (e) => {
      const wrap = e.target.closest(".playlist-swipe-wrap");
      const btn = e.target.closest(".swipe-action");

      if (wrap?.dataset.swipeOpen && !btn) {
        e.preventDefault();
        e.stopPropagation();
        wrap.querySelector(".playlist-row").style.transform = "";
        delete wrap.dataset.swipeOpen;
        return;
      }

      if (!btn) return;
      e.preventDefault();
      e.stopPropagation();

      const id = wrap?.dataset.id;
      const title = wrap?.dataset.title;

      if (btn.classList.contains("delete")) {
        BottomSheet.open("Удалить плейлист?", `
          <p style="color:var(--muted);margin:0 0 16px;font-size:14px;">Плейлист «${escapeHtml(title)}» будет удалён безвозвратно.</p>
          <button class="bs-btn danger" id="confirmDelPl">Удалить</button>
          <button class="bs-btn secondary" id="cancelDelPl">Отмена</button>
        `);
        document.getElementById("confirmDelPl")?.addEventListener("click", () => {
          const form = document.createElement("form");
          form.method = "post";
          form.action = `/api/playlists/${id}/delete`;
          document.body.appendChild(form);
          form.submit();
        });
        document.getElementById("cancelDelPl")?.addEventListener("click", () => BottomSheet.close());
      } else if (btn.classList.contains("rename")) {
        BottomSheet.open("Переименовать", `
          <input class="bs-input" id="renamePlInput" value="${escapeHtml(title || "")}" maxlength="100">
          <button class="bs-btn" id="confirmRenamePl">Сохранить</button>
        `);
        document.getElementById("confirmRenamePl")?.addEventListener("click", () => {
          const newTitle = document.getElementById("renamePlInput")?.value;
          if (!newTitle) return;
          const form = document.createElement("form");
          form.method = "post";
          form.action = `/api/playlists/${id}/rename`;
          form.innerHTML = `<input name="title" value="${escapeHtml(newTitle)}">`;
          document.body.appendChild(form);
          form.submit();
        });
      }
    });
  }

  async function checkImportStatus() {
    const importCard = document.getElementById("importProgressCard");
    if (!importCard) return;
    try {
      const res = await fetch("/api/playlists", { cache: "no-store" });
      const playlists = await res.json();
      const importing = playlists.find?.(p => p.import_status === "importing");
      if (importing) {
        importCard.hidden = false;
        document.getElementById("importProgressTitle").textContent = importing.title || "Импорт...";
        document.getElementById("importProgressSub").textContent = importing.track_count > 0 ? `Найдено ${importing.track_count} треков...` : "Импортируем...";
      } else {
        importCard.hidden = true;
      }
    } catch {
      importCard.hidden = true;
    }
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
})();

(() => {
  const storageStats = document.getElementById("storageStats");
  if (!storageStats) return;
  fetch("/api/storage", { cache: "no-store" })
    .then(r => r.json())
    .then(s => {
      storageStats.textContent = `Данные: ${s.data_human} · музыка: ${s.media_human} · обложки: ${s.covers_human} · тяжёлых: ${s.bulky_tracks ?? s.flac_tracks} · новые загрузки: ${s.quality}`;
    })
    .catch(() => { storageStats.textContent = "Не удалось прочитать хранилище."; });
})();
