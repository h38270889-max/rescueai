/**
 * ResQAI Global Client Application Script.
 * PWA Registration, Network Connectivity Telemetry, and Geolocation Helper.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Register Service Worker for PWA Offline Support
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/service-worker.js')
      .then((reg) => console.log('[ResQAI PWA] Service Worker registered:', reg.scope))
      .catch((err) => console.warn('[ResQAI PWA] Service Worker registration failed:', err));
  }

  // 2. Network Telemetry Listeners
  const updateNetworkStatus = () => {
    const isOnline = navigator.onLine;
    const pill = document.getElementById('network-status-pill');
    const banner = document.getElementById('offline-alert-banner');

    if (pill) {
      if (isOnline) {
        pill.className = 'status-pill online';
        pill.innerHTML = '<i class="bi bi-wifi"></i> Online';
      } else {
        pill.className = 'status-pill offline';
        pill.innerHTML = '<i class="bi bi-wifi-off"></i> Offline Mode';
      }
    }

    if (banner) {
      if (!isOnline) {
        banner.classList.add('active');
      } else {
        banner.classList.remove('active');
      }
    }
  };

  window.addEventListener('online', updateNetworkStatus);
  window.addEventListener('offline', updateNetworkStatus);
  updateNetworkStatus();

  // 3. Manual Sync Button Listener
  const manualSyncBtn = document.getElementById('btn-sync-offline');
  if (manualSyncBtn) {
    manualSyncBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      manualSyncBtn.disabled = true;
      manualSyncBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Syncing...';
      
      if (typeof syncOfflineReports === 'function') {
        const res = await syncOfflineReports();
        alert(`Synchronization Complete: ${res.synced} reports synced, ${res.failed} pending/failed.`);
        window.location.reload();
      }
      manualSyncBtn.disabled = false;
      manualSyncBtn.innerHTML = '<i class="bi bi-arrow-repeat me-1"></i> Sync Pending Reports';
    });
  }

  // 4. Geolocation Auto-Detection on Emergency Report Form
  const geoBtn = document.getElementById('btn-detect-location');
  if (geoBtn) {
    geoBtn.addEventListener('click', () => {
      if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser.');
        return;
      }

      geoBtn.disabled = true;
      geoBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Acquiring GPS...';

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const latInput = document.getElementById('latitude');
          const lngInput = document.getElementById('longitude');
          const addressInput = document.getElementById('location_address');

          if (latInput) latInput.value = position.coords.latitude.toFixed(6);
          if (lngInput) lngInput.value = position.coords.longitude.toFixed(6);
          if (addressInput && !addressInput.value) {
            addressInput.value = `GPS: ${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`;
          }

          geoBtn.disabled = false;
          geoBtn.innerHTML = '<i class="bi bi-check-circle-fill text-success me-1"></i> Location Acquired';
        },
        (error) => {
          console.warn('Geolocation error:', error);
          alert('Could not acquire location: ' + error.message);
          geoBtn.disabled = false;
          geoBtn.innerHTML = '<i class="bi bi-geo-alt me-1"></i> Detect Current GPS';
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
      );
    });
  }
});
