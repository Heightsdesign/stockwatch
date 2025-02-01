import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SubscriptionPlansPage } from './subscription-plans.page';

describe('SubscriptionPlansPage', () => {
  let component: SubscriptionPlansPage;
  let fixture: ComponentFixture<SubscriptionPlansPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(SubscriptionPlansPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
