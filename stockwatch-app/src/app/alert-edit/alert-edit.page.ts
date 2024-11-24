// src/app/alert-edit/alert-edit.page.ts

import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../services/api.service';
import { FormBuilder, FormGroup, Validators, FormArray } from '@angular/forms';
import { AlertController, LoadingController } from '@ionic/angular'; // **Optional:** For user feedback

@Component({
  selector: 'app-alert-edit',
  templateUrl: './alert-edit.page.html',
  styleUrls: ['./alert-edit.page.scss'],
})
export class AlertEditPage implements OnInit {
  alertId!: number;
  alert: any;
  editAlertForm!: FormGroup;
  indicators: any[] = [];
  indicatorLines: any[][] = []; // For each condition
  valueIndicatorLines: any[][] = [];

  loadIndicators() {
    this.apiService.getIndicators().subscribe((indicators) => {
      this.indicators = indicators;
    });
  }

  loadIndicatorLines(indicatorId: number, conditionIndex: number) {
    this.apiService.getIndicatorLinesByIndicatorId(indicatorId).subscribe((lines) => {
      this.indicatorLines[conditionIndex] = lines;
    });
  }

  loadValueIndicatorLines(indicatorId: number, conditionIndex: number) {
    if (indicatorId) {
      this.apiService.getIndicatorLinesByIndicatorId(indicatorId).subscribe((lines) => {
        this.valueIndicatorLines[conditionIndex] = lines;
      });
    }
  }

  // **Added:** Define check interval options
  checkIntervals = [
    { label: 'Every 1 Minute', value: 1 },
    { label: 'Every 5 Minutes', value: 5 },
    { label: 'Every 15 Minutes', value: 15 },
    { label: 'Every 30 Minutes', value: 30 },
    { label: 'Every Hour', value: 60 },
    { label: 'Once a Day', value: 1440 },
  ];

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private fb: FormBuilder,
    private router: Router,
    private alertController: AlertController, // **Optional:** For user feedback
    private loadingController: LoadingController // **Optional:** For loading indicators
  ) { }

  ngOnInit() {
    this.alertId = +this.route.snapshot.paramMap.get('id')!;
    this.loadAlertDetail();
  }

  loadAlertDetail() {
    this.apiService.getAlertDetail(this.alertId).subscribe(
      data => {
        this.alert = data;
        this.initializeForm();
      },
      error => {
        console.error('Error fetching alert detail:', error);
        // **Optional:** Handle error (e.g., navigate away or show a message)
      }
    );
  }

  get conditions(): FormArray {
    return this.editAlertForm.get('conditions') as FormArray;
  }

setConditionalValidators(conditionGroup: FormGroup, valueType: string | null) {
  // Clear existing validators
  conditionGroup.get('value_number')?.clearValidators();
  conditionGroup.get('value_indicator')?.clearValidators();
  conditionGroup.get('value_indicator_line')?.clearValidators();
  conditionGroup.get('value_timeframe')?.clearValidators();

  if (valueType === 'NUMBER') {
    conditionGroup.get('value_number')?.setValidators([Validators.required]);
  } else if (valueType === 'INDICATOR_LINE') {
    conditionGroup.get('value_indicator')?.setValidators([Validators.required]);
    conditionGroup.get('value_indicator_line')?.setValidators([Validators.required]);
    conditionGroup.get('value_timeframe')?.setValidators([Validators.required]);
  }

  // Update validity
  conditionGroup.get('value_number')?.updateValueAndValidity();
  conditionGroup.get('value_indicator')?.updateValueAndValidity();
  conditionGroup.get('value_indicator_line')?.updateValueAndValidity();
  conditionGroup.get('value_timeframe')?.updateValueAndValidity();
}

onIndicatorChange(event: any, conditionIndex: number) {
  const indicatorId = event.detail.value;
  this.loadIndicatorLines(indicatorId, conditionIndex);
}

onValueIndicatorChange(event: any, conditionIndex: number) {
  const indicatorId = event.detail.value;
  this.loadValueIndicatorLines(indicatorId, conditionIndex);
}

  initializeForm() {
    console.log('Initializing form for alert type:', this.alert.alert_type);

    if (this.alert.alert_type === 'PRICE') {
      this.editAlertForm = this.fb.group({
        target_price: [this.alert.target_price, Validators.required],
        condition: [this.alert.condition, Validators.required],
        check_interval: [this.alert.check_interval, [Validators.required, Validators.min(1)]],
        is_active: [this.alert.is_active],
      });
    } else if (this.alert.alert_type === 'PERCENT_CHANGE') {
      this.editAlertForm = this.fb.group({
        percentage_change: [this.alert.percentage_change_alert.percentage_change, Validators.required],
        direction: [this.alert.percentage_change_alert.direction, Validators.required],
        lookback_period: [this.alert.percentage_change_alert.lookback_period, Validators.required],
        custom_lookback_days: [this.alert.percentage_change_alert.custom_lookback_days],
        check_interval: [this.alert.check_interval, [Validators.required, Validators.min(1)]],
        is_active: [this.alert.is_active],
      });

      // Handle changes to 'lookback_period'
      this.editAlertForm.get('lookback_period')?.valueChanges.subscribe(value => {
        if (value === 'CUSTOM') {
          this.editAlertForm.get('custom_lookback_days')?.setValidators([Validators.required, Validators.min(1)]);
        } else {
          this.editAlertForm.get('custom_lookback_days')?.clearValidators();
          this.editAlertForm.get('custom_lookback_days')?.setValue(null);
        }
        this.editAlertForm.get('custom_lookback_days')?.updateValueAndValidity();
      });
    } else if (this.alert.alert_type === 'INDICATOR_CHAIN') {
      this.editAlertForm = this.fb.group({
        is_active: [this.alert.is_active],
        check_interval: [this.alert.check_interval, [Validators.required, Validators.min(1)]],
        conditions: this.fb.array([]),
      });

      // Load indicators and indicator lines (if not already loaded)
      this.loadIndicators();

      // Populate the conditions
      if (this.alert.indicator_chain_alert && this.alert.indicator_chain_alert.conditions) {
        this.alert.indicator_chain_alert.conditions.forEach((condition: any) => {
          const conditionGroup = this.createConditionGroup(condition);
          this.conditions.push(conditionGroup);
          this.loadIndicatorLines(condition.indicator, this.conditions.length - 1);
          this.loadValueIndicatorLines(condition.value_indicator, this.conditions.length - 1);
        });
      }
    } else {
      console.error('Unknown alert type:', this.alert.alert_type);
    }
  }

  createConditionGroup(condition?: any): FormGroup {
    const conditionGroup = this.fb.group({
      id: [condition?.id],
      position_in_chain: [condition?.position_in_chain || this.conditions.length + 1, Validators.required],
      indicator: [condition?.indicator, Validators.required],
      indicator_line: [condition?.indicator_line, Validators.required],
      indicator_timeframe: [condition?.indicator_timeframe, Validators.required],
      condition_operator: [condition?.condition_operator, Validators.required],
      value_type: [condition?.value_type, Validators.required],
      value_number: [condition?.value_number],
      value_indicator: [condition?.value_indicator],
      value_indicator_line: [condition?.value_indicator_line],
      value_timeframe: [condition?.value_timeframe],
    });

    // Set up value_type change listener
    conditionGroup.get('value_type')?.valueChanges.subscribe((valueType) => {
      this.setConditionalValidators(conditionGroup, valueType);
    });

    // Set conditional validators based on existing value_type
    this.setConditionalValidators(conditionGroup, condition?.value_type);

    return conditionGroup;
  }

  addCondition() {
    this.conditions.push(this.createConditionGroup());
  }

  removeCondition(index: number) {
    this.conditions.removeAt(index);
  }

  submitForm() {
    if (this.editAlertForm.valid) {
      const formValue = this.editAlertForm.value;

      let updatedData: any = {
        is_active: formValue.is_active,
        stock: this.alert.stock,
      };

      if (this.alert.alert_type === 'PRICE') {
        updatedData.target_price = formValue.target_price;
        updatedData.condition = formValue.condition;
        updatedData.check_interval = formValue.check_interval;

      } else if (this.alert.alert_type === 'PERCENT_CHANGE') {
        updatedData.percentage_change = formValue.percentage_change;
        updatedData.direction = formValue.direction;
        updatedData.lookback_period = formValue.lookback_period;
        updatedData.custom_lookback_days = formValue.lookback_period === 'CUSTOM' ? formValue.custom_lookback_days : null;
        updatedData.check_interval = formValue.check_interval;

      } else if (this.alert.alert_type === 'INDICATOR_CHAIN') {
        updatedData.conditions = formValue.conditions.map((condition: any) => ({
          id: condition.id,
          position_in_chain: condition.position_in_chain,
          indicator: condition.indicator,
          indicator_line: condition.indicator_line || null,
          indicator_timeframe: condition.indicator_timeframe,
          condition_operator: condition.condition_operator,
          value_type: condition.value_type,
          value_number: condition.value_number || null,
          value_indicator: condition.value_indicator || null,
          value_indicator_line: condition.value_indicator_line || null,
          value_timeframe: condition.value_timeframe || null,
        }));
      }

      this.apiService.updateAlert(this.alertId, updatedData).subscribe(
        async () => {
          console.log('Alert updated successfully:', Response);
          // **Optional:** Show success message
          const successAlert = await this.alertController.create({
            header: 'Success',
            message: 'Alert updated successfully.',
            buttons: ['OK'],
          });
          await successAlert.present();

          this.router.navigate(['/alert-detail', this.alertId]);
        },
        async (error) => {
          console.error('Error updating alert:', error);
          // **Optional:** Show error message
          const errorAlert = await this.alertController.create({
            header: 'Error',
            message: 'Failed to update alert.',
            buttons: ['OK'],
          });
          await errorAlert.present();
        }
      );
    } else {
      // **Optional:** Inform the user that the form is invalid
      this.alertController.create({
        header: 'Invalid Form',
        message: 'Please ensure all required fields are filled correctly.',
        buttons: ['OK'],
      }).then(alert => alert.present());
    }
  }
}
