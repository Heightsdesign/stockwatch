import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { SubscriptionPlansPageRoutingModule } from './subscription-plans-routing.module';

import { SubscriptionPlansPage } from './subscription-plans.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    SubscriptionPlansPageRoutingModule
  ],
  declarations: [SubscriptionPlansPage]
})
export class SubscriptionPlansPageModule {}
