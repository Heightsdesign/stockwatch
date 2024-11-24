import { ComponentFixture, TestBed } from '@angular/core/testing';
import { StockDetailsPage } from './stock-details.page';

describe('StockDetailsPage', () => {
  let component: StockDetailsPage;
  let fixture: ComponentFixture<StockDetailsPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(StockDetailsPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
