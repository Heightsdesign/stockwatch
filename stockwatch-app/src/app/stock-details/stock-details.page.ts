import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormControl, FormGroup, FormArray, Validators } from '@angular/forms';
import { ApiService } from '../services/api.service';
import { AlertController, LoadingController } from '@ionic/angular';
import { Observable } from 'rxjs';
import { IndicatorParameter } from '../interfaces/indicator-parameter.interface';

@Component({
  selector: 'app-stock-details',
  templateUrl: './stock-details.page.html',
  styleUrls: ['./stock-details.page.scss'],
})

export class StockDetailsPage implements OnInit {
  stock = { symbol: '', name: '' };
  indicators: any[] = [];
  indicatorLines: any[][] = []; // For each condition, we have a list of indicator lines
  alertForm!: FormGroup;
  valueIndicatorLines: any[][] = [];
  indicatorParameters: { [key: number]: any[] } = {};
  valueIndicatorParameters: { [key: number]: IndicatorParameter[] } = {};


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
    private fb: FormBuilder,
    private apiService: ApiService,
    private alertController: AlertController,
    private loadingController: LoadingController,
    private router: Router
  ) {}

  ngOnInit() {
    const symbol = this.route.snapshot.paramMap.get('symbol');
    if (symbol) {
      this.loadStockDetails(symbol);
    } else {
      console.error('Symbol is null');
      this.router.navigate(['/']);
    }

    this.initializeForm();
    this.loadIndicators();

    // Subscribe to alert_type changes to handle form control validations
    this.alertForm.get('alert_type')?.valueChanges.subscribe((value) => {
      this.onAlertTypeChange(value);
    });
  }

  initializeForm() {
    this.alertForm = this.fb.group({
      stock_symbol: ['', Validators.required],
      alert_type: ['PRICE', Validators.required],

      // **Price Target Alert Fields**
      target_price: [''], // Existing field at root level
      condition: [''], // **Added:** Condition field

      // **Check Interval Field**
      check_interval: [60, [Validators.required, Validators.min(1)]], // **Added:** Check Interval field with default value

      // Fields for Percentage Change Alert
      reference_price: [''],
      lookback_period: [''],
      custom_lookback_days: [''],
      direction: ['UP'],
      percentage_change: [''],

      // Fields for Indicator Chain Alert
      conditions: this.fb.array([]),
    });

    // Set initial validators
    this.setValidatorsForAlertType('PRICE');
  }

  loadStockDetails(symbol: string) {
    this.apiService.getStockDetails(symbol).subscribe((stock) => {
      this.stock = stock;
      // Update stock symbol in the form
      this.alertForm.patchValue({ stock_symbol: stock.symbol });
    });
  }

  loadIndicators() {
    this.apiService.getIndicators().subscribe((indicators) => {
      this.indicators = indicators;
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


  get conditions(): FormArray {
    return this.alertForm.get('conditions') as FormArray;
  }

  get conditionFormGroups(): FormGroup[] {
    return this.conditions.controls as FormGroup[];
  }

  createConditionGroup(): FormGroup {
    const conditionGroup = this.fb.group({
      position_in_chain: [this.conditions.length + 1, Validators.required],
      indicator: ['', Validators.required],
      indicator_line: ['', Validators.required],
      indicator_timeframe: ['', Validators.required],
      condition_operator: ['', Validators.required],
      value_type: ['', Validators.required],
      value_number: [null],
      value_indicator: [''],
      value_indicator_line: [''],
      value_timeframe: [''],
      value_parameters: this.fb.group({}),
      parameters: this.fb.group({}),
    });

    // Set up value_type change listener
    conditionGroup.get('value_type')?.valueChanges.subscribe((valueType) => {
      this.setConditionalValidators(conditionGroup, valueType);
    });

    return conditionGroup;
  }


  addCondition() {
    const conditionGroup = this.createConditionGroup();
    this.conditions.push(conditionGroup);
    this.indicatorLines.push([]); // Initialize indicator lines array for this condition
  }

  removeCondition(index: number) {
    this.conditions.removeAt(index);
    this.indicatorLines.splice(index, 1);
  }

  onIndicatorChange(event: any, conditionIndex: number) {
    const indicatorName = event.detail.value;
    console.log(`Indicator changed for condition ${conditionIndex}, indicatorName: ${indicatorName}`);

    const indicator = this.indicators.find((ind) => ind.name === indicatorName);

    // Declare conditionGroup once
    const conditionGroup = this.conditions.at(conditionIndex) as FormGroup;

    if (indicator) {
      // Set indicator lines
      this.indicatorLines[conditionIndex] = indicator.lines;

      // Initialize parameter controls
      const parameters = indicator.parameters || [];

      // Create a FormGroup for parameters
      const parametersGroup = this.fb.group({});
      parameters.forEach((param: any) => {
        parametersGroup.addControl(
          param.name,
          new FormControl(
            param.default_value || '', // Use default value if available
            param.required ? Validators.required : [] // Add Validators if required
          )
        );
      });
      // Set the 'parameters' FormGroup in the condition group
      conditionGroup.setControl('parameters', parametersGroup);

      // Store parameters for the template
      this.indicatorParameters[conditionIndex] = parameters;
    } else {
      // Handle case where indicator is not found
      this.indicatorLines[conditionIndex] = [];

      // Remove the 'parameters' FormGroup if it exists
      if (conditionGroup.contains('parameters')) {
        conditionGroup.removeControl('parameters');
      }
      this.indicatorParameters[conditionIndex] = [];
    }
  }


onValueIndicatorChange(event: any, conditionIndex: number) {

  console.log("[DEBUG] onValueIndicatorChange triggered for condition", conditionIndex, "with indicator:", event.detail.value);
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


  onAlertTypeChange(alertType: string) {
    // Reset validators for relevant controls
    this.resetValidators();

    // Clear existing conditions if alert type changes
    this.conditions.clear();
    this.indicatorLines = [];
    this.valueIndicatorLines = [];

    // Set validators based on alert type
    this.setValidatorsForAlertType(alertType);

    // Update form validity
    this.alertForm.updateValueAndValidity();

    // For INDICATOR_CHAIN, initialize conditions if empty
    if (alertType === 'INDICATOR_CHAIN' && this.conditions.length === 0) {
      this.addCondition();
    }
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

  resetValidators() {
    const controlNames = [
      'target_price',
      'condition', // **Added:** Include condition in reset
      'reference_price',
      'lookback_period',
      'custom_lookback_days',
      'direction',
      'percentage_change',
      'check_interval', // **Added:** Reset check_interval if necessary
    ];

    controlNames.forEach(controlName => {
      const control = this.alertForm.get(controlName);
      control?.clearValidators();
      control?.updateValueAndValidity();
    });
  }

  setValidatorsForAlertType(alertType: string) {
    if (alertType === 'PRICE') {
      this.alertForm.get('target_price')?.setValidators([Validators.required]);
      this.alertForm.get('condition')?.setValidators([Validators.required]);
      this.alertForm.get('check_interval')?.setValidators([Validators.required, Validators.min(1)]);
    } else if (alertType === 'PERCENT_CHANGE') {
      this.alertForm.get('percentage_change')?.setValidators([Validators.required]);
      this.alertForm.get('direction')?.setValidators([Validators.required]);
      this.alertForm.get('lookback_period')?.setValidators([Validators.required]);
      this.alertForm.get('check_interval')?.setValidators([Validators.required, Validators.min(1)]);
    } else if (alertType === 'INDICATOR_CHAIN') {
      this.alertForm.get('check_interval')?.setValidators([Validators.required, Validators.min(1)]);
      // Conditions have their own validators
    }

    // Update validity after setting validators
    this.alertForm.get('target_price')?.updateValueAndValidity();
    this.alertForm.get('condition')?.updateValueAndValidity();
    this.alertForm.get('check_interval')?.updateValueAndValidity();
    this.alertForm.get('percentage_change')?.updateValueAndValidity();
    this.alertForm.get('direction')?.updateValueAndValidity();
    this.alertForm.get('lookback_period')?.updateValueAndValidity();
  }

  async onSubmit() {
    this.alertForm.markAllAsTouched();
    if (this.alertForm.invalid) {
      // Show validation errors
      const alert = await this.alertController.create({
        header: 'Validation Error',
        message: 'Please fill in all required fields.',
        buttons: ['OK'],
      });
      await alert.present();
      return;
    }

    const loading = await this.loadingController.create();
    await loading.present();

    const alertType = this.alertForm.get('alert_type')?.value;
    const alertData = this.prepareAlertData();

    let createAlertObservable: Observable<any>;
    switch (alertType) {
      case 'PRICE':
        createAlertObservable = this.apiService.createPriceTargetAlert(alertData);
        break;
      case 'PERCENT_CHANGE':
        createAlertObservable = this.apiService.createPercentageChangeAlert(alertData);
        break;
      case 'INDICATOR_CHAIN':
        createAlertObservable = this.apiService.createIndicatorChainAlert(alertData);
        break;
      default:
        console.error(`Unknown alert type: ${alertType}`);
        await loading.dismiss();
        return;
    }

    createAlertObservable.subscribe(
      async () => {
        // success handling
        await loading.dismiss();
      },

      async (error) => {
        console.error('Error creating alert:', error);

        if (error.status === 400 && error.error) {
          // 1) Possibly handle top-level fields if you have them
          if (error.error.check_interval) {
            this.alertForm.get('check_interval')?.setErrors({
              customError: error.error.check_interval.join(' '),
            });
          }

          // 2) Now handle conditions array
          if (Array.isArray(error.error.conditions)) {
            error.error.conditions.forEach((condErr: any, idx: number) => {
              // condErr might be { "length": ["Maximum allowed length is 400."] }
              const conditionGroup = this.conditions.at(idx) as FormGroup;

              // If 'length' key is present
              if (condErr.length) {
                const lengthCtrl = conditionGroup.get('parameters')?.get('length');
                if (lengthCtrl) {
                  lengthCtrl.setErrors({ customError: condErr.length.join(' ') });
                }
              }

              // If there are other keys, handle them similarly...
            });
          }

          // Show a top-level alert if you like
          const alertPopup = await this.alertController.create({
            header: 'Validation Error',
            message: 'Please correct the highlighted fields.',
            buttons: ['OK'],
          });
          await alertPopup.present();
          await loading.dismiss();

        } else {
          // Non-400 error
          const errorAlert = await this.alertController.create({
            header: 'Error',
            message: 'Failed to create alert.',
            buttons: ['OK'],
          });
          await errorAlert.present();
        }
      }
    );
  }

  prepareAlertData() {

    console.log("[DEBUG] Form Values before prepareAlertData:", this.alertForm.value);
    const formValues = this.alertForm.value;
    const stockSymbol = this.stock.symbol;

    const alert = {
      stock: stockSymbol,
      is_active: true,
      check_interval: formValues.check_interval,
      alert_type: formValues.alert_type,
    };

    switch (formValues.alert_type) {
      case 'PRICE':
        return {
          ...alert,
          target_price: formValues.target_price,
          condition: formValues.condition,
        };
      case 'PERCENT_CHANGE':
        return {
          ...alert,
          percentage_change: formValues.percentage_change,
          direction: formValues.direction,
          lookback_period: formValues.lookback_period,
          custom_lookback_days:
            formValues.lookback_period === 'CUSTOM' ? formValues.custom_lookback_days : null,
        };
      case 'INDICATOR_CHAIN':
        return {
          ...alert,
          conditions: this.conditions.controls.map((control, index) => {
            const conditionGroup = control as FormGroup; // Explicitly cast the control to FormGroup
            const condition = conditionGroup.value;

            const conditionData: any = {
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

              // Get value_indicator_parameters from FormGroup
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
                } else {
                  convertedValueParameters[paramName] = value;
                }
              });

              conditionData.value_indicator_parameters = convertedValueParameters;
            }

            // Convert indicator_parameters
            const parametersGroup = conditionGroup.get('parameters') as FormGroup;
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
              } else {
                convertedParameters[paramName] = value;
              }
            });

            conditionData.indicator_parameters = convertedParameters;

            return conditionData;
          }),
        };
      default:
        throw new Error(`Unknown alert type: ${formValues.alert_type}`);
    }
  }
  private applyInlineErrors(errorObj: any) {
    // Suppose the DRF error might look like:
    // {
    //   "conditions": {
    //     "0": {
    //       "indicator_parameters": {
    //         "length": ["Max is 400"]
    //       }
    //     }
    //   }
    //   "check_interval": ["Must be >= 1"]
    //   ...
    // }

    // 1) Top-level fields
    if (errorObj.check_interval && Array.isArray(errorObj.check_interval)) {
      const ctrl = this.alertForm.get('check_interval');
      if (ctrl) {
        ctrl.setErrors({ customError: errorObj.check_interval.join(' ') });
      }
    }
    if (errorObj.target_price && Array.isArray(errorObj.target_price)) {
      const ctrl = this.alertForm.get('target_price');
      if (ctrl) {
        ctrl.setErrors({ customError: errorObj.target_price.join(' ') });
      }
    }
    // etc. for other top-level fields like 'condition', 'lookback_period' ...

    // 2) If "conditions" is in error object
    if (errorObj.conditions && typeof errorObj.conditions === 'object') {
      const conditionsErrors = errorObj.conditions;
      // Each key is like "0", "1", ...
      Object.keys(conditionsErrors).forEach((idxStr) => {
        const idx = parseInt(idxStr, 10);
        const conditionErrorObj = conditionsErrors[idxStr];

        // Our form array
        const conditionGroup = this.conditions.at(idx) as FormGroup;

        // Possibly the entire condition has errors:
        if (Array.isArray(conditionErrorObj)) {
          // e.g. "conditions.0": ["some error..."]
          conditionGroup.setErrors({ customError: conditionErrorObj.join(' ') });
        }
        else if (typeof conditionErrorObj === 'object') {
          // We might see "indicator": ["can't be blank"] or "indicator_parameters": {...}

          // If "indicator" key is present
          if (conditionErrorObj.indicator && Array.isArray(conditionErrorObj.indicator)) {
            const c = conditionGroup.get('indicator');
            c?.setErrors({ customError: conditionErrorObj.indicator.join(' ') });
          }
          // If "indicator_parameters" has an object like { "length": ["Max 400"] }
          if (conditionErrorObj.indicator_parameters) {
            this.applyIndicatorParametersErrors(conditionGroup, conditionErrorObj.indicator_parameters);
          }
          // Similarly check "value_indicator_parameters" if that’s how DRF returns it
        }
      });
    }
  }

  private applyIndicatorParametersErrors(conditionGroup: FormGroup, paramErrors: any) {
    // paramErrors might look like { "length": ["Maximum allowed length is 400."] }
    const parametersGroup = conditionGroup.get('parameters') as FormGroup;
    if (!parametersGroup) return;

    Object.keys(paramErrors).forEach((paramName) => {
      const messages = paramErrors[paramName];
      if (Array.isArray(messages)) {
        const paramCtrl = parametersGroup.get(paramName);
        if (paramCtrl) {
          paramCtrl.setErrors({ customError: messages.join(' ') });
        }
      }
    });
  }
}


