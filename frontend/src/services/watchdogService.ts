import { api } from './api';

export interface WatchdogProgress {
  drug_id: number;
  status: 'queued' | 'running' | 'completed' | 'error';
  message: string;
  progress: number;
  timestamp: string;
  data?: {
    has_update?: boolean;
    current_version?: number;
    new_version?: number;
    changes?: string;
    s3_url?: string;
  };
}

export type ProgressCallback = (progress: WatchdogProgress) => void;

class WatchdogService {
  private ws: WebSocket | null = null;
  private progressCallbacks: Map<number, ProgressCallback> = new Map();

  /**
   * Connect to WebSocket for real-time progress updates
   */
  connect(onProgress: ProgressCallback): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/watchdog/ws';
      
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected for real-time progress');
        resolve();
        
        // Send ping every 30 seconds to keep connection alive
        setInterval(() => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send('ping');
          }
        }, 30000);
      };

      this.ws.onmessage = (event) => {
        try {
          const progress: WatchdogProgress = JSON.parse(event.data);
          console.log('📊 Progress update:', progress);
          
          // Call the progress callback
          onProgress(progress);
          
          // Also call drug-specific callback if registered
          const drugCallback = this.progressCallbacks.get(progress.drug_id);
          if (drugCallback) {
            drugCallback(progress);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        reject(error);
      };

      this.ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        this.ws = null;
      };
    });
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.progressCallbacks.clear();
  }

  /**
   * Register a progress callback for a specific drug
   */
  onDrugProgress(drugId: number, callback: ProgressCallback) {
    this.progressCallbacks.set(drugId, callback);
  }

  /**
   * Trigger manual version check for multiple drugs
   * Make sure to connect() first to receive progress updates
   */
  async triggerManualCheck(drugIds: number[]): Promise<any> {
    try {
      // Backend expects a list directly, not an object
      const response = await api.post('/watchdog/trigger', drugIds);
      return response.data;
    } catch (error: any) {
      console.error('Error triggering watchdog:', error);
      const errorMessage = error.response?.data?.detail 
        || error.message 
        || 'Failed to trigger automation';
      throw new Error(errorMessage);
    }
  }

  /**
   * Run watchdog for a single drug (synchronous, waits for completion)
   * Use this if you don't want WebSocket real-time updates
   */
  async runForDrug(drugId: number): Promise<any> {
    try {
      const response = await api.post(`/watchdog/run/${drugId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error running watchdog:', error);
      throw new Error(error.response?.data?.detail || 'Failed to run automation');
    }
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Export singleton instance
export const watchdogService = new WatchdogService();
