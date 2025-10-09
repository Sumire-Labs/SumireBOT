/**
 * Pterodactyl Panel API Client
 * Manages Pterodactyl server operations
 */

export interface PterodactylConfig {
  url: string;
  apiKey: string;
}

export interface PterodactylServer {
  identifier: string;
  uuid: string;
  name: string;
  description: string;
  status: string | null;
  limits: {
    memory: number;
    disk: number;
    cpu: number;
  };
}

export interface ServerListResponse {
  data: {
    attributes: PterodactylServer;
  }[];
}

export interface PowerSignal {
  signal: 'start' | 'stop' | 'restart' | 'kill';
}

export class PterodactylClient {
  private config: PterodactylConfig;

  constructor(config: PterodactylConfig) {
    this.config = config;
  }

  /**
   * Get authorization headers for API requests
   */
  private getHeaders(): Record<string, string> {
    return {
      'Authorization': `Bearer ${this.config.apiKey}`,
      'Content-Type': 'application/json',
      'Accept': 'Application/vnd.pterodactyl.v1+json',
    };
  }

  /**
   * Get list of all servers
   */
  async getServers(): Promise<PterodactylServer[]> {
    const response = await fetch(`${this.config.url}/api/client`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch servers: ${response.statusText}`);
    }

    const data = await response.json() as ServerListResponse;
    return data.data.map(item => item.attributes);
  }

  /**
   * Get server details
   */
  async getServer(serverId: string): Promise<PterodactylServer> {
    const response = await fetch(`${this.config.url}/api/client/servers/${serverId}`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch server: ${response.statusText}`);
    }

    const data = await response.json() as { attributes: PterodactylServer };
    return data.attributes;
  }

  /**
   * Send power signal to server
   */
  async sendPowerSignal(serverId: string, signal: PowerSignal['signal']): Promise<void> {
    const response = await fetch(`${this.config.url}/api/client/servers/${serverId}/power`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ signal }),
    });

    if (!response.ok) {
      throw new Error(`Failed to send power signal: ${response.statusText}`);
    }
  }

  /**
   * Get server resource usage
   */
  async getServerResources(serverId: string) {
    const response = await fetch(`${this.config.url}/api/client/servers/${serverId}/resources`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch server resources: ${response.statusText}`);
    }

    const data = await response.json() as {
      attributes: {
        current_state: string;
        resources: {
          cpu_absolute: number;
          memory_bytes: number;
          disk_bytes: number;
          network_tx_bytes: number;
          network_rx_bytes: number;
        };
      };
    };
    return data.attributes;
  }
}
