// src/app/app-routing.module.ts

import { NgModule } from '@angular/core';
import { PreloadAllModules, RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  },
  {
    path: 'login',
    loadChildren: () => import('./pages/login/login.module').then( m => m.LoginPageModule)
  },
  {
    path: 'home',
    loadChildren: () => import('./home/home.module').then( m => m.HomePageModule)
  },
  {
    path: 'signup',
    loadChildren: () => import('./pages/signup/signup.module').then( m => m.SignupPageModule)
  },
  // Add other routes here
  {
    path: 'stock-details/:symbol',
    loadChildren: () => import('./stock-details/stock-details.module').then(m => m.StockDetailsPageModule),
  },
  {
    path: 'stock-details',
    loadChildren: () => import('./stock-details/stock-details.module').then( m => m.StockDetailsPageModule)
  },
  {
    path: 'alert-detail/:id',
    loadChildren: () => import('./alert-detail/alert-detail.module').then(m => m.AlertDetailPageModule)
  },
  {
    path: 'alert-edit',
    loadChildren: () => import('./alert-edit/alert-edit.module').then( m => m.AlertEditPageModule)
  },
  {
    path: 'alert-edit/:id',
    loadChildren: () => import('./alert-edit/alert-edit.module').then(m => m.AlertEditPageModule)
  },
  {
    path: 'account',
    loadChildren: () => import('./account/account.module').then( m => m.AccountPageModule)
  },
];

@NgModule({
  imports: [
    RouterModule.forRoot(routes, { preloadingStrategy: PreloadAllModules })
  ],
  exports: [RouterModule]
})
export class AppRoutingModule { }
