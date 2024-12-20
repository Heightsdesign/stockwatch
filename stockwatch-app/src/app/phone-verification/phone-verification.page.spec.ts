import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PhoneVerificationPage } from './phone-verification.page';

describe('PhoneVerificationPage', () => {
  let component: PhoneVerificationPage;
  let fixture: ComponentFixture<PhoneVerificationPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(PhoneVerificationPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
