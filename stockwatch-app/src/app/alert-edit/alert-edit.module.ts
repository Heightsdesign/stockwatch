import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms'; // Import ReactiveFormsModule
import { IonicModule } from '@ionic/angular';



import { AlertEditPageRoutingModule } from './alert-edit-routing.module';

import { AlertEditPage } from './alert-edit.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule, // Add ReactiveFormsModule here
    IonicModule,
    AlertEditPageRoutingModule
  ],
  declarations: [AlertEditPage],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class AlertEditPageModule {}
