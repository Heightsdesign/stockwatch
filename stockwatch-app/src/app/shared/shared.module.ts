// src/app/shared/shared.module.ts

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NavbarComponent } from '../navbar/navbar.component';
import { IonicModule } from '@ionic/angular';
import { RouterModule } from '@angular/router'; // Import RouterModule

@NgModule({
  declarations: [NavbarComponent],
  imports: [
    CommonModule,
    IonicModule,
    RouterModule // Add RouterModule here
  ],
  exports: [NavbarComponent]
})
export class SharedModule {}
