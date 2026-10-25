/**
 * ResQAI IndexedDB Offline Queue and Synchronization Engine.
 * Persists emergency reports locally during cellular/internet blackouts.
 * Automatically synchronizes via Idempotency Keys when connection is restored.
 */

const DB_NAME = 'ResQAIOfflineDB';
const DB_VERSION = 1;
const STORE_NAME = 'queued_reports';

function openResQAIDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'idempotency_key' });
        store.createIndex('sync_status', 'sync_status', { unique: false });
        store.createIndex('created_at', 'created_at', { unique: false });
      }
    };

    request.onsuccess = (event) => resolve(event.target.result);
    request.onerror = (event) => reject(event.target.error);
  });
}

/**
 * Generate a client-side UUID v4 to serve as an idempotency key.
 */
function generateIdempotencyKey() {
  if (crypto && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'resq-' + Date.now() + '-' + Math.random().toString(36).substring(2, 9);
}

/**
 * Store an emergency report draft in IndexedDB.
 */
async function saveReportToOfflineQueue(reportData) {
  const db = await openResQAIDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORE_NAME], 'readwrite');
    const store = tx.objectStore(STORE_NAME);

    const record = {
      idempotency_key: reportData.idempotency_key || generateIdempotencyKey(),
      category: reportData.category,
      description: reportData.description,
      original_language: reportData.original_language || 'en',
      contact_name: reportData.contact_name || '',
      contact_phone: reportData.contact_phone || '',
      location_address: reportData.location_address || '',
      latitude: reportData.latitude || null,
      longitude: reportData.longitude || null,
      affected_count: reportData.affected_count || 1,
      sync_status: 'pending', // 'pending' | 'synced' | 'failed'
      incident_id: null,
      created_at: new Date().toISOString()
    };

    const request = store.put(record);
    request.onsuccess = () => {
      updatePendingBadge();
      resolve(record);
    };
    request.onerror = (e) => reject(e.target.error);
  });
}

/**
 * Retrieve all reports currently stored in IndexedDB.
 */
async function getAllOfflineReports() {
  const db = await openResQAIDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORE_NAME], 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result || []);
    request.onerror = (e) => reject(e.target.error);
  });
}

/**
 * Update the sync status and assigned incident_id of a queued report.
 */
async function updateReportSyncStatus(idempotencyKey, status, incidentId = null) {
  const db = await openResQAIDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORE_NAME], 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const getReq = store.get(idempotencyKey);

    getReq.onsuccess = () => {
      const record = getReq.result;
      if (record) {
        record.sync_status = status;
        if (incidentId) record.incident_id = incidentId;
        store.put(record);
      }
      resolve();
    };
    getReq.onerror = (e) => reject(e.target.error);
  });
}

/**
 * Delete a synced or obsolete report from IndexedDB.
 */
async function deleteOfflineReport(idempotencyKey) {
  const db = await openResQAIDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORE_NAME], 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const req = store.delete(idempotencyKey);
    req.onsuccess = () => {
      updatePendingBadge();
      resolve();
    };
    req.onerror = (e) => reject(e.target.error);
  });
}

/**
 * Synchronize all pending offline reports with the backend server.
 */
async function syncOfflineReports() {
  if (!navigator.onLine) {
    console.log('[ResQAI Sync] Device is still offline. Skipping synchronization.');
    return { synced: 0, failed: 0, message: 'Device is offline' };
  }

  const reports = await getAllOfflineReports();
  const pendingReports = reports.filter(r => r.sync_status === 'pending');

  if (pendingReports.length === 0) {
    return { synced: 0, failed: 0, message: 'No pending reports to sync' };
  }

  console.log(`[ResQAI Sync] Attempting to sync ${pendingReports.length} queued reports...`);
  let syncedCount = 0;
  let failedCount = 0;

  for (const report of pendingReports) {
    try {
      const response = await fetch('/api/sync/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(report)
      });

      if (response.ok) {
        const result = await response.json();
        await updateReportSyncStatus(report.idempotency_key, 'synced', result.incident_id);
        syncedCount++;
        console.log(`[ResQAI Sync] Report synced successfully as ${result.incident_id}`);
      } else {
        await updateReportSyncStatus(report.idempotency_key, 'failed');
        failedCount++;
      }
    } catch (err) {
      console.warn(`[ResQAI Sync] Network failure syncing report ${report.idempotency_key}:`, err);
      await updateReportSyncStatus(report.idempotency_key, 'failed');
      failedCount++;
    }
  }

  updatePendingBadge();
  return { synced: syncedCount, failed: failedCount };
}

/**
 * Update UI notification badge showing pending unsynced drafts count.
 */
async function updatePendingBadge() {
  try {
    const reports = await getAllOfflineReports();
    const pending = reports.filter(r => r.sync_status === 'pending');
    const badge = document.getElementById('offline-sync-badge');
    const syncBtn = document.getElementById('btn-sync-offline');

    if (badge) {
      badge.textContent = pending.length;
      badge.style.display = pending.length > 0 ? 'inline-block' : 'none';
    }
    if (syncBtn) {
      syncBtn.style.display = pending.length > 0 ? 'inline-flex' : 'none';
    }
  } catch (err) {
    console.warn('Could not update offline badge:', err);
  }
}

// Global Event Listeners for Automatic Background Sync
window.addEventListener('online', () => {
  console.log('[ResQAI] Internet connection restored. Initiating automatic synchronization...');
  syncOfflineReports().then((res) => {
    if (res && res.synced > 0) {
      alert(`Connection Restored: ${res.synced} offline emergency reports were successfully synced to responders!`);
      window.location.reload();
    }
  });
});

document.addEventListener('DOMContentLoaded', () => {
  updatePendingBadge();
});
