import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../services/api.service';
import { AlertController } from '@ionic/angular';

@Component({
  selector: 'app-alert-detail',
  templateUrl: './alert-detail.page.html',
  styleUrls: ['./alert-detail.page.scss'],
})
export class AlertDetailPage implements OnInit {
  alertId!: number;
  alert: any;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private router: Router,
    private alertController: AlertController
  ) {}

  ngOnInit() {
    this.alertId = +this.route.snapshot.paramMap.get('id')!;
    this.loadAlertDetail();
  }

  loadAlertDetail() {
    this.apiService.getAlertDetail(this.alertId).subscribe(
      data => {
        this.alert = data;
        console.log('Alert Detail:', this.alert);
      },
      error => {
        console.error('Error fetching alert detail:', error);
      }
    );
  }

  editAlert() {
    this.router.navigate(['/alert-edit', this.alertId]);
  }

  async confirmDeleteAlert() {
    const alert = await this.alertController.create({
      header: 'Confirm Delete',
      message: 'Are you sure you want to delete this alert?',
      buttons: [
        {
          text: 'Cancel',
          role: 'cancel',
        },
        {
          text: 'Delete',
          handler: () => {
            this.deleteAlert();
          },
        },
      ],
    });

    await alert.present();
  }

  deleteAlert() {
    this.apiService.deleteAlert(this.alertId).subscribe(
      () => {
        console.log('Alert deleted successfully');
        this.router.navigate(['/home']);
      },
      (error: any) => {
        console.error('Error deleting alert:', error);
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
}
