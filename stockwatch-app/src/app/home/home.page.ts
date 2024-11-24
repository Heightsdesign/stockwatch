// src/app/home/home.page.ts

import { Component, OnInit } from '@angular/core';
import { Stock } from '../models/stock.model';
import { ApiService } from '../services/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-home',
  templateUrl: './home.page.html',
  styleUrls: ['./home.page.scss'],
})
export class HomePage implements OnInit {
  userStocks: Stock[] = [];
  allStocks: Stock[] = [];
  filteredStocks: Stock[] = [];
  searchTerm = '';
  userAlerts: any[] = [];

  constructor(private apiService: ApiService, private router: Router) {}

  ngOnInit() {
    this.loadUserStocks();
    this.loadAllStocks();
    this.loadUserAlerts();
  }

  loadUserStocks() {
    this.apiService.getUserAlerts().subscribe((alerts: any[]) => {
      // Assuming alerts have a stock property with symbol and name
      const stockSymbols = Array.from(new Set(alerts.map((alert) => alert.stock.symbol)));
      this.userStocks = stockSymbols.map((symbol: string) => ({ symbol, name: symbol }));
    });
  }

  loadAllStocks() {
    this.apiService.getAllStocks().subscribe((stocks: Stock[]) => {
      this.allStocks = stocks;
    });
  }

  filterStocks() {
    const term = this.searchTerm.toLowerCase();
    this.filteredStocks = this.allStocks.filter((stock: Stock) =>
      stock.symbol.toLowerCase().includes(term) || stock.name.toLowerCase().includes(term)
    );
  }

  goToStockDetails(stock: Stock) {
    this.router.navigate(['/stock-details', stock.symbol]);
  }

  loadUserAlerts() {
    this.apiService.getUserAlerts().subscribe(
      data => {
        this.userAlerts = data;
        console.log('User Alerts:', this.userAlerts);
      },
      error => {
        console.error('Error fetching user alerts:', error);
      }
    );
  }

  getLookbackPeriod(alert: any): string {
    if (alert.lookback_period !== 'CUSTOM') {
      return alert.lookback_period;
    } else {
      return `${alert.custom_lookback_days} days`;
    }
  }

  goToAlertDetail(alert: any) {
    // Navigate to the alert detail page (to be implemented)
    console.log('Alert clicked:', alert);
    this.router.navigate(['/alert-detail', alert.id]);
  }
}
