import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { PhoneVerificationPageRoutingModule } from './phone-verification-routing.module';

import { PhoneVerificationPage } from './phone-verification.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    PhoneVerificationPageRoutingModule
  ],
  declarations: [PhoneVerificationPage]
})
export class PhoneVerificationPageModule {}
