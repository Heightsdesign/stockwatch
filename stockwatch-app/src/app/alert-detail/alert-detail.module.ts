import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { AlertDetailPageRoutingModule } from './alert-detail-routing.module';

import { AlertDetailPage } from './alert-detail.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    AlertDetailPageRoutingModule
  ],
  declarations: [AlertDetailPage]
})
export class AlertDetailPageModule {}
