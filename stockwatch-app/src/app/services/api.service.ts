// src/app/services/api.service.ts

import { Injectable } from '@angular/core';
import { HttpClient,  HttpHeaders} from '@angular/common/http';
import { Observable } from 'rxjs';
import { Stock } from '../models/stock.model';



@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private apiUrl = 'http://localhost:8000/api';
  private credsUrl = 'http://localhost:8000/creds';

  constructor(private http: HttpClient) {}

  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('auth_token');
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': `Token ${token}`,
    });
  }

  login(credentials: { email: string; password: string }): Observable<any> {
    return this.http.post<any>(`${this.credsUrl}/api-token-auth/`, credentials);
  }

  // Add other methods as needed
  signup(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/registration/`, data);
  }

  getStockDetails(symbol: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/stocks/${symbol}/`);
  }

  createPriceTargetAlert(data: any): Observable<any> {
    const headers = this.getAuthHeaders();
    return this.http.post<any>(`${this.apiUrl}/price-target-alerts/`, data);
  }

  createPercentageChangeAlert(data: any): Observable<any> {
    const headers = this.getAuthHeaders();
    return this.http.post<any>(`${this.apiUrl}/percentage-change-alerts/`, data);
  }

  createIndicatorChainAlert(data: any): Observable<any> {
    const headers = this.getAuthHeaders();
    return this.http.post<any>(`${this.apiUrl}/indicator-chain-alerts/`, data);
  }

  getUserAlerts(): Observable<any> {
    return this.http.get(`${this.apiUrl}/user-alerts/`);
  }

  getAllStocks(): Observable<Stock[]> {
    return this.http.get<Stock[]>(`${this.apiUrl}/stocks/`);
  }

  getIndicators(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/indicators/`);
  }

  getIndicatorLines(indicatorId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/indicator-lines/?indicator=${indicatorId}`);
  }

  getAlertDetail(alertId: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/alerts/${alertId}/`);
  }

  deleteAlert(alertId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/alerts/${alertId}/`);
  }

  updateAlert(alertId: number, data: any): Observable<any> {
    const token = localStorage.getItem('auth_token');
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': `Token ${token}`,
    });
    return this.http.put(`${this.apiUrl}/alerts/${alertId}/`, data, { headers });
  }

  getIndicatorLinesByIndicatorId(indicatorId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/indicator-lines/?indicator_id=${indicatorId}`);
  }

  getUserProfile(): Observable<any> {
    const headers = this.getAuthHeaders();
    return this.http.get<any>(`${this.credsUrl}/profile/`, { headers });
  }

  updateUserProfile(data: any): Observable<any> {
    const headers = this.getAuthHeaders();
    return this.http.put<any>(`${this.credsUrl}/profile/`, data, { headers });
  }


  getCountries(): Observable<any[]> {
    return this.http.get<any[]>(`${this.credsUrl}/countries/`);
  }


  registerDeviceToken(data: { device_token: string }): Observable<any> {
    return this.http.post(`${this.credsUrl}/api-register-device-token/`, data);
  }


}
