/**
 * API client for communicating with the backend.
 */

import axios, { AxiosInstance } from 'axios';
import { AnalyzeResponse, MapConfig, ErrorDetail } from '../types/analysis';

class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL = '/api') {
    this.client = axios.create({
      baseURL,
      timeout: 120000, // 2 minutes for demo analysis
    });
  }

  /**
   * Upload a demo file and analyze it.
   */
  async analyzeDemoFile(
    demoFile: File,
    steam64: string,
    mapName: string = 'de_dust2',
    windowSeconds: number = 30,
  ): Promise<AnalyzeResponse> {
    const formData = new FormData();
    formData.append('demo', demoFile);
    formData.append('steam64', steam64);
    formData.append('map_name', mapName);
    formData.append('window_seconds', windowSeconds.toString());

    try {
      const response = await this.client.post<AnalyzeResponse>('/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        throw new Error(
          `Player ${steam64} not found in demo. Available players: ${error.response.data.players?.map((p: any) => p.name).join(', ')}`
        );
      }
      throw error;
    }
  }

  /**
   * Get a previously saved result by task ID.
   */
  async getResult(taskId: string): Promise<AnalyzeResponse> {
    const response = await this.client.get<AnalyzeResponse>(`/results/${taskId}`);
    return response.data;
  }

  /**
   * Get de_dust2 map configuration.
   */
  async getMapConfig(): Promise<MapConfig> {
    const response = await this.client.get<MapConfig>('/maps/de_dust2/config');
    return response.data;
  }

  /**
   * Get de_dust2 radar image URL.
   */
  getRadarImageUrl(): string {
    return `${this.client.defaults.baseURL}/maps/de_dust2/radar`;
  }
}

export const apiClient = new ApiClient();
