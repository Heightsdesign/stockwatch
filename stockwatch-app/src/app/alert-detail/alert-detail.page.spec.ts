import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AlertDetailPage } from './alert-detail.page';

describe('AlertDetailPage', () => {
  let component: AlertDetailPage;
  let fixture: ComponentFixture<AlertDetailPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(AlertDetailPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
