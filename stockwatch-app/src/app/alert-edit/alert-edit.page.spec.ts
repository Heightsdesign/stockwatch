import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AlertEditPage } from './alert-edit.page';

describe('AlertEditPage', () => {
  let component: AlertEditPage;
  let fixture: ComponentFixture<AlertEditPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(AlertEditPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
