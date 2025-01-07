// src/app/alert-edit/alert-edit.page.ts

import { Component, OnInit } from '@angular/core';
import { forkJoin } from 'rxjs';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../services/api.service';
import { FormBuilder, FormControl, FormGroup, Validators, FormArray } from '@angular/forms';
import { AlertController, LoadingController } from '@ionic/angular'; // **Optional:** For user feedback
import { IndicatorParameter } from '../interfaces/indicator-parameter.interface';


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
  indicatorParameters: { [key: number]: IndicatorParameter[] } = {};
  valueIndicatorParameters: { [key: number]: IndicatorParameter[] } = {};

  private applyInlineErrors(errors: any) {
    if (errors.conditions) {
      Object.keys(errors.conditions).forEach((index) => {
        const conditionErrors = errors.conditions[index];
        const conditionGroup = this.conditions.at(Number(index)) as FormGroup;

        // Handle specific errors for parameters like 'length'
        if (conditionErrors?.indicator_parameters?.length) {
          const msg = conditionErrors.indicator_parameters.length.join(' ');
          const lengthCtrl = conditionGroup.get('parameters')?.get('length');
          if (lengthCtrl) {
            lengthCtrl.setErrors({ customError: msg });
          }
        }

        // Apply other condition-level errors
        Object.keys(conditionErrors).forEach((fieldKey) => {
          const control = conditionGroup.get(fieldKey);
          if (control) {
            const errorMsgArray = conditionErrors[fieldKey];
            control.setErrors({ customError: errorMsgArray.join(' ') });
          }
        });
      });
    }
  }
  /**
   * Applies inline errors to the "parameters" formGroup inside a condition,
   * matching keys with the respective parameter controls.
   */
  private applyIndicatorParametersErrors(conditionGroup: FormGroup, paramErrors: any) {
    // paramErrors might look like { "length": ["Max is 400"], "anotherParam": ["invalid"] }
    const parametersGroup = conditionGroup.get('parameters') as FormGroup;
    if (!parametersGroup) return;

    // For each param name in paramErrors
    Object.keys(paramErrors).forEach((paramName) => {
      const paramMessages = paramErrors[paramName];
      if (Array.isArray(paramMessages)) {
        // "length": ["Maximum allowed length is 400."]
        const paramCtrl = parametersGroup.get(paramName);
        if (paramCtrl) {
          paramCtrl.setErrors({ customError: paramMessages.join(' ') });
        }
      }
    });
  }
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

  loadValueIndicatorLines(indicatorName: string, conditionIndex: number) {
  const indicator = this.indicators.find(ind => ind.name === indicatorName);
  if (indicator) {
    this.valueIndicatorLines[conditionIndex] = indicator.lines;
  } else {
    this.valueIndicatorLines[conditionIndex] = [];
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
    forkJoin({
      indicators: this.apiService.getIndicators(),
      alertDetail: this.apiService.getAlertDetail(this.alertId),
    }).subscribe(({ indicators, alertDetail }) => {
      this.indicators = indicators;
      this.alert = alertDetail;
      this.initializeForm();
    });
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

  get conditionFormGroups(): FormGroup[] {
    return this.conditions.controls as FormGroup[];
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
    const indicatorName = event.detail.value;
    const indicator = this.indicators.find((ind) => ind.name === indicatorName);

    const conditionGroup = this.conditions.at(conditionIndex) as FormGroup;

    if (indicator) {
      // Set indicator lines
      this.indicatorLines[conditionIndex] = indicator.lines;

      // Initialize parameter controls
      const parameters: IndicatorParameter[] = indicator.parameters || [];

      const parametersGroup = this.fb.group({});
      parameters.forEach((param: IndicatorParameter) => {
        parametersGroup.addControl(
          param.name,
          new FormControl(
            param.default_value || '',
            param.required ? Validators.required : []
          )
        );
      });
      conditionGroup.setControl('parameters', parametersGroup);
      this.indicatorParameters[conditionIndex] = parameters;
    } else {
      // Handle case where indicator is not found
      this.indicatorLines[conditionIndex] = [];
      if (conditionGroup.contains('parameters')) {
        conditionGroup.removeControl('parameters');
      }
      this.indicatorParameters[conditionIndex] = [];
    }
  }

  onValueIndicatorChange(event: any, conditionIndex: number) {
    const indicatorName = event.detail.value;
    const indicator = this.indicators.find(ind => ind.name === indicatorName);

    const conditionGroup = this.conditions.at(conditionIndex) as FormGroup;

    if (indicator) {
      // Load value indicator lines
      this.loadValueIndicatorLines(indicatorName, conditionIndex);

      // Initialize parameter controls for value_indicator
      const parameters: IndicatorParameter[] = indicator.parameters || [];

      const valueParametersGroup = this.fb.group({});
      parameters.forEach((param: IndicatorParameter) => {
        valueParametersGroup.addControl(
          param.name,
          new FormControl(
            param.default_value || '',
            param.required ? Validators.required : []
          )
        );
      });

      conditionGroup.setControl('value_parameters', valueParametersGroup);

      // Store parameters for the template
      this.valueIndicatorParameters[conditionIndex] = parameters;
    } else {
      // Handle case where indicator is not found
      this.valueIndicatorLines[conditionIndex] = [];
      if (conditionGroup.contains('value_parameters')) {
        conditionGroup.removeControl('value_parameters');
      }
      this.valueIndicatorParameters[conditionIndex] = [];
    }
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

      // Populate the conditions
      if (this.alert.indicator_chain_alert && this.alert.indicator_chain_alert.conditions) {
        this.alert.indicator_chain_alert.conditions.forEach((condition: any, index: number) => {
          const conditionGroup = this.createConditionGroup(condition);
          this.conditions.push(conditionGroup);

          // Load indicator data (lines and parameters)
          this.loadIndicatorDataForCondition(index, condition);

          // Load value indicator lines and parameters if necessary
          if (condition.value_indicator) {
            this.loadValueIndicatorLines(condition.value_indicator, index);

            // Initialize value indicator parameters
            const valueIndicator = this.indicators.find(ind => ind.name === condition.value_indicator);
            if (valueIndicator) {
              // Set value indicator lines
              this.valueIndicatorLines[index] = valueIndicator.lines;

              const valueParameters: IndicatorParameter[] = valueIndicator.parameters || [];

              const valueParametersGroup = this.fb.group({});
              valueParameters.forEach((param: IndicatorParameter) => {
                valueParametersGroup.addControl(
                  param.name,
                  new FormControl(
                    condition.value_indicator_parameters
                      ? condition.value_indicator_parameters[param.name]
                      : param.default_value || '',
                    param.required ? Validators.required : []
                  )
                );
              });

              const conditionGroup = this.conditions.at(index) as FormGroup;
              conditionGroup.setControl('value_parameters', valueParametersGroup);

              // Store parameters for the template
              this.valueIndicatorParameters[index] = valueParameters;
            }
          }
        });
      }
    } else {
      console.error('Unknown alert type:', this.alert.alert_type);
    }
}

loadIndicatorDataForCondition(index: number, condition: any) {
  const indicatorName = condition.indicator;
  const indicator = this.indicators.find((ind) => ind.name === indicatorName);

  const conditionGroup = this.conditions.at(index) as FormGroup;

  if (indicator) {
    // Set indicator lines
    this.indicatorLines[index] = indicator.lines;

    // Initialize parameter controls
    const parameters: IndicatorParameter[] = indicator.parameters || [];

    const parametersGroup = this.fb.group({});
    parameters.forEach((param: IndicatorParameter) => {
      parametersGroup.addControl(
        param.name,
        new FormControl(
          condition.indicator_parameters ? condition.indicator_parameters[param.name] : param.default_value || '',
          param.required ? Validators.required : []
        )
      );
    });
    conditionGroup.setControl('parameters', parametersGroup);
    this.indicatorParameters[index] = parameters;
  } else {
    // Handle case where indicator is not found
    this.indicatorLines[index] = [];
    if (conditionGroup.contains('parameters')) {
      conditionGroup.removeControl('parameters');
    }
    this.indicatorParameters[index] = [];
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
      parameters: this.fb.group({}),
      value_parameters: this.fb.group({}),
    });

    // Set up value_type change listener
    conditionGroup.get('value_type')?.valueChanges.subscribe((valueType) => {
      this.setConditionalValidators(conditionGroup, valueType);
    });

    // Set conditional validators based on existing value_type
    this.setConditionalValidators(conditionGroup, condition?.value_type);

    // If condition has existing parameters, initialize them
    if (condition && condition.indicator_parameters) {
      const parametersGroup = conditionGroup.get('parameters') as FormGroup;
      Object.keys(condition.indicator_parameters).forEach((paramName) => {
        parametersGroup.addControl(
          paramName,
          new FormControl(condition.indicator_parameters[paramName])
        );
      });
    }
    return conditionGroup;
  }

  addCondition() {
    this.conditions.push(this.createConditionGroup());
  }

  removeCondition(index: number) {
    this.conditions.removeAt(index);
  }

  async submitForm() {
    if (this.editAlertForm.valid) {
      const formValue = this.editAlertForm.value;

      // Add this line to inspect form values
      console.log('Form Value:', JSON.stringify(formValue, null, 2));

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
        updatedData.conditions = formValue.conditions.map((condition: any, index: number) => {
          const conditionData: any = {
            id: condition.id,
            position_in_chain: condition.position_in_chain,
            indicator: condition.indicator,
            indicator_line: condition.indicator_line || null,
            indicator_timeframe: condition.indicator_timeframe,
            condition_operator: condition.condition_operator,
            value_type: condition.value_type,
          };

          // Include value fields based on value_type
          if (condition.value_type === 'NUMBER') {
            conditionData.value_number = parseFloat(condition.value_number);
          } else if (condition.value_type === 'INDICATOR_LINE') {
            conditionData.value_indicator = condition.value_indicator;
            conditionData.value_indicator_line = condition.value_indicator_line;
            conditionData.value_timeframe = condition.value_timeframe;

            // Convert value_indicator parameters to correct data types
            const conditionGroup = this.conditions.at(index) as FormGroup;
            const valueParametersGroup = conditionGroup.get('value_parameters') as FormGroup;
            const valueParameterValues = valueParametersGroup ? valueParametersGroup.value : {};
            const valueParameterDefinitions = this.valueIndicatorParameters[index] || [];

            const convertedValueParameters: { [key: string]: any } = {};
            valueParameterDefinitions.forEach((paramDef: IndicatorParameter) => {
              const paramName = paramDef.name;
              let value = valueParameterValues[paramName];

              // Convert value based on param_type
              if (paramDef.param_type === 'int') {
                convertedValueParameters[paramName] = parseInt(value, 10);
              } else if (paramDef.param_type === 'float') {
                convertedValueParameters[paramName] = parseFloat(value);
              } else if (paramDef.param_type === 'string' || paramDef.param_type === 'choice') {
                convertedValueParameters[paramName] = value;
              } else {
                // Default to string if type is unknown
                convertedValueParameters[paramName] = value;
              }
            });

            conditionData.value_indicator_parameters = convertedValueParameters;
          }
          // For 'PRICE', no additional value fields are needed

          // Convert indicator parameters to correct data types
          const parametersGroup = (this.conditions.at(index) as FormGroup).get('parameters') as FormGroup;
          const parameterValues = parametersGroup ? parametersGroup.value : {};
          const parameterDefinitions = this.indicatorParameters[index] || [];

          const convertedParameters: { [key: string]: any } = {};
          parameterDefinitions.forEach((paramDef: IndicatorParameter) => {
            const paramName = paramDef.name;
            let value = parameterValues[paramName];

            // Convert value based on param_type
            if (paramDef.param_type === 'int') {
              convertedParameters[paramName] = parseInt(value, 10);
            } else if (paramDef.param_type === 'float') {
              convertedParameters[paramName] = parseFloat(value);
            } else if (paramDef.param_type === 'string' || paramDef.param_type === 'choice') {
              convertedParameters[paramName] = value;
            } else {
              // Default to string if type is unknown
              convertedParameters[paramName] = value;
            }
          });

          conditionData.indicator_parameters = convertedParameters;

          return conditionData;
        });

        updatedData.check_interval = formValue.check_interval;
      }

    this.apiService.updateAlert(this.alertId, updatedData).subscribe(
      async () => {
        // Success
        console.log('Alert updated successfully');
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

        if (error.status === 400 && error.error) {
          // Backend error parsing
          console.log('DEBUG: Backend error response', error.error);

          if (error.error.conditions) {
            Object.keys(error.error.conditions).forEach((index) => {
              const conditionErrors = error.error.conditions[index];
              console.log(`DEBUG: Processing condition index ${index}`, conditionErrors);

              const conditionGroup = this.conditions.at(Number(index)) as FormGroup;

              if (!conditionGroup) {
                console.warn(`WARNING: No conditionGroup found at index ${index}`);
                return;
              }

              // Log condition group structure
              console.log(`DEBUG: Condition Group at index ${index}`, conditionGroup.value);

              // Handle `indicator_parameters.length` error
              if (conditionErrors?.length) {
                const msg = conditionErrors.length.join(' ');

                // Locate the 'length' control within the 'parameters' group
                const parametersGroup = conditionGroup.get('parameters') as FormGroup;
                if (parametersGroup) {
                  const lengthCtrl = parametersGroup.get('length');
                  if (lengthCtrl) {
                    console.log('DEBUG: Found length control, applying error');
                    lengthCtrl.setErrors({ customError: msg });
                  } else {
                    console.warn('WARNING: Length control not found in parameters group');
                  }
                } else {
                  console.warn('WARNING: Parameters group not found in condition group');
                }
              }

              // Handle other condition-level errors
              Object.keys(conditionErrors).forEach((fieldKey) => {
                const control = conditionGroup.get(fieldKey);
                if (control) {
                  const errorMsgArray = conditionErrors[fieldKey];
                  control.setErrors({ customError: errorMsgArray.join(' ') });
                } else {
                  console.warn(`WARNING: Control for fieldKey "${fieldKey}" not found`);
                }
              });
            });
          }

          // Show a validation error modal
          const errorAlert = await this.alertController.create({
            header: 'Validation Error',
            message: 'Please correct the highlighted fields.',
            buttons: ['OK'],
          });
          await errorAlert.present();
        } else {
          // Handle general errors
          const errorAlert = await this.alertController.create({
            header: 'Error',
            message: 'Failed to update alert.',
            buttons: ['OK'],
          });
          await errorAlert.present();
        }
      }
    );

    }
  }
}
