import { Component, OnInit } from '@angular/core';
import { ApiService } from '../services/api.service';
import { AlertController } from '@ionic/angular';

@Component({
  selector: 'app-subscription-plans',
  templateUrl: './subscription-plans.page.html',
  styleUrls: ['./subscription-plans.page.scss'],
})
export class SubscriptionPlansPage implements OnInit {
  plans: any[] = [];

  constructor(
    private apiService: ApiService,
    private alertController: AlertController
  ) {}

  ngOnInit() {
    this.apiService.getSubscriptionPlans().subscribe(
      (data: any[]) => {
        this.plans = data; // e.g. [{name: 'Free', ...}, {name: 'Silver', ...}]
      },
      async (error: any) => { // explicitly type error as any
        const alert = await this.alertController.create({
          header: 'Error',
          message: 'Failed to load plans.',
          buttons: ['OK'],
        });
        await alert.present();
      }
    );
  }

  selectPlan(plan: any) {
    // For now, just show an alert or navigate to a payment page
    // e.g. this.router.navigate(['/payment', plan.id])
    console.log('Selected plan:', plan);
  }
}
