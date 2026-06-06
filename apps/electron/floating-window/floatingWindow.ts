/** Floating window logic for Electron always-on-top timer display. */

// DOM elements
const activityNameEl = document.getElementById('activity-name') as HTMLDivElement;
const timerDisplayEl = document.getElementById('timer-display') as HTMLDivElement;
const dragHandleEl = document.getElementById('drag-handle') as HTMLDivElement;
const closeBtnEl = document.getElementById('close-btn') as HTMLSpanElement;
const opacitySliderEl = document.getElementById('opacity-slider') as HTMLInputElement;

// Timer state
let currentElapsed = 0;
let timerInterval: ReturnType<typeof setInterval> | null = null;

/**
 * Format seconds into HH:MM:SS display string.
 */
function formatDuration(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

/**
 * Start the timer display with a given elapsed time.
 */
function startTimer(elapsedSeconds: number): void {
  currentElapsed = elapsedSeconds;
  if (timerInterval) clearInterval(timerInterval);

  timerDisplayEl.textContent = formatDuration(currentElapsed);

  timerInterval = setInterval(() => {
    currentElapsed += 1;
    timerDisplayEl.textContent = formatDuration(currentElapsed);
  }, 1000);
}

/**
 * Stop the timer and reset the display.
 */
function stopTimer(): void {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
  activityNameEl.textContent = 'No activity running';
  timerDisplayEl.textContent = '00:00:00';
}

// Listen for timer updates from main process
if (window.electronAPI) {
  window.electronAPI.onTimerUpdate((data: { name: string; elapsed: string }) => {
    activityNameEl.textContent = data.name || 'No activity running';

    // Parse elapsed time string back to seconds
    const parts = data.elapsed.split(':');
    if (parts.length === 3) {
      const seconds = parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2]);
      startTimer(seconds);
    } else {
      stopTimer();
    }
  });
}

// Drag handling
let isDragging = false;
let lastX = 0;
let lastY = 0;

dragHandleEl.addEventListener('mousedown', (e: MouseEvent) => {
  isDragging = true;
  lastX = e.screenX;
  lastY = e.screenY;
});

document.addEventListener('mousemove', (e: MouseEvent) => {
  if (!isDragging) return;
  const deltaX = e.screenX - lastX;
  const deltaY = e.screenY - lastY;
  lastX = e.screenX;
  lastY = e.screenY;

  if (window.electronAPI) {
    window.electronAPI.startDragging(deltaX, deltaY);
  }
});

document.addEventListener('mouseup', () => {
  isDragging = false;
});

// Close button
closeBtnEl.addEventListener('click', () => {
  window.close();
});

// Opacity control
opacitySliderEl.addEventListener('input', (e: Event) => {
  const target = e.target as HTMLInputElement;
  const opacity = parseInt(target.value) / 100;
  if (window.electronAPI) {
    window.electronAPI.setFloatingOpacity(opacity);
  }
});
