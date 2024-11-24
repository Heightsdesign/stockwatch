import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { AlertDetailPage } from './alert-detail.page';

const routes: Routes = [
  {
    path: '',
    component: AlertDetailPage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class AlertDetailPageRoutingModule {}
