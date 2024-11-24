import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { StockDetailsPageRoutingModule } from './stock-details-routing.module';

import { StockDetailsPage } from './stock-details.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    IonicModule,
    StockDetailsPageRoutingModule
  ],
  declarations: [StockDetailsPage]
})
export class StockDetailsPageModule {}
