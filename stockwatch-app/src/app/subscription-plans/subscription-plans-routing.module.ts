import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { SubscriptionPlansPage } from './subscription-plans.page';

const routes: Routes = [
  {
    path: '',
    component: SubscriptionPlansPage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class SubscriptionPlansPageRoutingModule {}
