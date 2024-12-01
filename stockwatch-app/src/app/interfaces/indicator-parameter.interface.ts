export interface IndicatorParameter {
  name: string;
  display_name: string;
  param_type: string;
  required: boolean;
  default_value?: any;
  choices?: string[];
}
